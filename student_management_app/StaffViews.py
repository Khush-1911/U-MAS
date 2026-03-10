import json

from django.conf import settings
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from student_management_app.models import Subjects, SessionYearModel, Students, Attendance, AttendanceReport, \
    LeaveReportStaff, Staffs, FeedBackStaffs, CustomUser, Courses, NotificationStaffs, StudentResult, OnlineClassRoom
from student_management_app.services.live_class_service import (
    create_or_get_active_room,
    end_room,
    issue_realtime_token,
    mark_participant_joined,
    serialize_room_state,
)


def _logged_in_staff(request):
    return Staffs.objects.get(admin=request.user.id)


def _subject_for_staff_or_none(subject_id, request_user_id):
    return Subjects.objects.filter(id=subject_id, staff_id=request_user_id).first()


def _assigned_student_or_none(student_admin_id, staff_obj):
    return Students.objects.filter(
        admin=student_admin_id,
        assigned_staff=staff_obj,
    ).first()


def staff_home(request):
    #For Fetch All Student Under Staff
    staff_obj = _logged_in_staff(request)
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    students_qs=Students.objects.filter(assigned_staff=staff_obj)
    students_count=students_qs.count()

    #Fetch All Attendance Count
    attendance_count=Attendance.objects.filter(subject_id__in=subjects).count()

    #Fetch All Approve Leave
    leave_count=LeaveReportStaff.objects.filter(staff_id=staff_obj.id,leave_status=1).count()
    subject_count=subjects.count()

    #Fetch Attendance Data by Subject
    subject_list=[]
    attendance_list=[]
    for subject in subjects:
        attendance_count1=Attendance.objects.filter(subject_id=subject.id).count()
        subject_list.append(subject.subject_name)
        attendance_list.append(attendance_count1)

    students_attendance=students_qs
    student_list=[]
    student_list_attendance_present=[]
    student_list_attendance_absent=[]
    for student in students_attendance:
        attendance_present_count=AttendanceReport.objects.filter(status=True,student_id=student.id).count()
        attendance_absent_count=AttendanceReport.objects.filter(status=False,student_id=student.id).count()
        student_list.append(student.admin.username)
        student_list_attendance_present.append(attendance_present_count)
        student_list_attendance_absent.append(attendance_absent_count)

    return render(request,"staff_template/staff_home_template.html",{"students_count":students_count,"attendance_count":attendance_count,"leave_count":leave_count,"subject_count":subject_count,"subject_list":subject_list,"attendance_list":attendance_list,"student_list":student_list,"present_list":student_list_attendance_present,"absent_list":student_list_attendance_absent})

def staff_take_attendance(request):
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    session_years=SessionYearModel.object.all()
    return render(request,"staff_template/staff_take_attendance.html",{"subjects":subjects,"session_years":session_years})

@csrf_exempt
def get_students(request):
    subject_id=request.POST.get("subject")
    session_year=request.POST.get("session_year")

    subject=_subject_for_staff_or_none(subject_id, request.user.id)
    if not subject:
        return JsonResponse({"error": "Invalid subject for this staff"}, status=403)

    session_model=SessionYearModel.object.filter(id=session_year).first()
    if not session_model:
        return JsonResponse({"error": "Session not found"}, status=404)

    staff_obj = _logged_in_staff(request)
    students=Students.objects.filter(
        course_id=subject.course_id,
        session_year_id=session_model,
        assigned_staff=staff_obj,
    )
    list_data=[]

    for student in students:
        data_small={"id":student.admin.id,"name":student.admin.first_name+" "+student.admin.last_name}
        list_data.append(data_small)
    return JsonResponse(json.dumps(list_data),content_type="application/json",safe=False)

@csrf_exempt
def save_attendance_data(request):
    student_ids=request.POST.get("student_ids")
    subject_id=request.POST.get("subject_id")
    attendance_date=request.POST.get("attendance_date")
    session_year_id=request.POST.get("session_year_id")

    subject_model=_subject_for_staff_or_none(subject_id, request.user.id)
    session_model=SessionYearModel.object.filter(id=session_year_id).first()
    if not subject_model or not session_model:
        return HttpResponse("ERR")

    staff_obj = _logged_in_staff(request)
    json_sstudent=json.loads(student_ids)

    try:
        with transaction.atomic():
            attendance=Attendance(subject_id=subject_model,attendance_date=attendance_date,session_year_id=session_model)
            attendance.save()

            for stud in json_sstudent:
                 student=_assigned_student_or_none(stud['id'], staff_obj)
                 if student is None:
                     raise ValueError("Unauthorized student in attendance payload")
                 attendance_report=AttendanceReport(student_id=student,attendance_id=attendance,status=stud['status'])
                 attendance_report.save()
        return HttpResponse("OK")
    except Exception:
        return HttpResponse("ERR")

def staff_update_attendance(request):
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    session_year_id=SessionYearModel.object.all()
    return render(request,"staff_template/staff_update_attendance.html",{"subjects":subjects,"session_year_id":session_year_id})

@csrf_exempt
def get_attendance_dates(request):
    subject=request.POST.get("subject")
    session_year_id=request.POST.get("session_year_id")
    subject_obj=_subject_for_staff_or_none(subject, request.user.id)
    session_year_obj=SessionYearModel.object.filter(id=session_year_id).first()
    if not subject_obj or not session_year_obj:
        return JsonResponse(json.dumps([]),safe=False)

    attendance=Attendance.objects.filter(subject_id=subject_obj,session_year_id=session_year_obj)
    attendance_obj=[]
    for attendance_single in attendance:
        data={"id":attendance_single.id,"attendance_date":str(attendance_single.attendance_date),"session_year_id":attendance_single.session_year_id.id}
        attendance_obj.append(data)

    return JsonResponse(json.dumps(attendance_obj),safe=False)

@csrf_exempt
def get_attendance_student(request):
    attendance_date=request.POST.get("attendance_date")
    attendance=Attendance.objects.filter(id=attendance_date).first()
    if not attendance or attendance.subject_id.staff_id_id != request.user.id:
        return JsonResponse(json.dumps([]),content_type="application/json",safe=False)

    attendance_data=AttendanceReport.objects.filter(attendance_id=attendance)
    staff_obj = _logged_in_staff(request)
    list_data=[]

    for student in attendance_data:
        if student.student_id.assigned_staff_id != staff_obj.id:
            continue
        data_small={"id":student.student_id.admin.id,"name":student.student_id.admin.first_name+" "+student.student_id.admin.last_name,"status":student.status}
        list_data.append(data_small)
    return JsonResponse(json.dumps(list_data),content_type="application/json",safe=False)

@csrf_exempt
def save_updateattendance_data(request):
    student_ids=request.POST.get("student_ids")
    attendance_date=request.POST.get("attendance_date")
    attendance=Attendance.objects.filter(id=attendance_date).first()
    if not attendance or attendance.subject_id.staff_id_id != request.user.id:
        return HttpResponse("ERR")

    json_sstudent=json.loads(student_ids)
    staff_obj = _logged_in_staff(request)


    try:
        for stud in json_sstudent:
             student=_assigned_student_or_none(stud['id'], staff_obj)
             if student is None:
                 raise ValueError("Unauthorized student in attendance payload")
             attendance_report=AttendanceReport.objects.get(student_id=student,attendance_id=attendance)
             attendance_report.status=stud['status']
             attendance_report.save()
        return HttpResponse("OK")
    except:
        return HttpResponse("ERR")

def staff_apply_leave(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    leave_data=LeaveReportStaff.objects.filter(staff_id=staff_obj)
    return render(request,"staff_template/staff_apply_leave.html",{"leave_data":leave_data})

def staff_apply_leave_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("staff_apply_leave"))
    else:
        leave_date=request.POST.get("leave_date")
        leave_msg=request.POST.get("leave_msg")

        staff_obj=Staffs.objects.get(admin=request.user.id)
        try:
            leave_report=LeaveReportStaff(staff_id=staff_obj,leave_date=leave_date,leave_message=leave_msg,leave_status=0)
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("staff_apply_leave"))
        except:
            messages.error(request, "Failed To Apply for Leave")
            return HttpResponseRedirect(reverse("staff_apply_leave"))


def staff_feedback(request):
    staff_id=Staffs.objects.get(admin=request.user.id)
    feedback_data=FeedBackStaffs.objects.filter(staff_id=staff_id)
    return render(request,"staff_template/staff_feedback.html",{"feedback_data":feedback_data})

def staff_feedback_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("staff_feedback_save"))
    else:
        feedback_msg=request.POST.get("feedback_msg")

        staff_obj=Staffs.objects.get(admin=request.user.id)
        try:
            feedback=FeedBackStaffs(staff_id=staff_obj,feedback=feedback_msg,feedback_reply="")
            feedback.save()
            messages.success(request, "Successfully Sent Feedback")
            return HttpResponseRedirect(reverse("staff_feedback"))
        except:
            messages.error(request, "Failed To Send Feedback")
            return HttpResponseRedirect(reverse("staff_feedback"))

def staff_profile(request):
    user=CustomUser.objects.get(id=request.user.id)
    staff=Staffs.objects.get(admin=user)
    return render(request,"staff_template/staff_profile.html",{"user":user,"staff":staff})

def staff_profile_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("staff_profile"))
    else:
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        address=request.POST.get("address")
        password=request.POST.get("password")
        try:
            customuser=CustomUser.objects.get(id=request.user.id)
            customuser.first_name=first_name
            customuser.last_name=last_name
            if password!=None and password!="":
                customuser.set_password(password)
            customuser.save()

            staff=Staffs.objects.get(admin=customuser.id)
            staff.address=address
            staff.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("staff_profile"))
        except:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("staff_profile"))

@csrf_exempt
def staff_fcmtoken_save(request):
    token=request.POST.get("token")
    try:
        staff=Staffs.objects.get(admin=request.user.id)
        staff.fcm_token=token
        staff.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")

def staff_all_notification(request):
    staff=Staffs.objects.get(admin=request.user.id)
    notifications=NotificationStaffs.objects.filter(staff_id=staff.id)
    return render(request,"staff_template/all_notification.html",{"notifications":notifications})

def staff_add_result(request):
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    session_years=SessionYearModel.object.all()
    return render(request,"staff_template/staff_add_result.html",{"subjects":subjects,"session_years":session_years})

def save_student_result(request):
    if request.method!='POST':
        return HttpResponseRedirect('staff_add_result')
    student_admin_id=request.POST.get('student_list')
    assignment_marks=request.POST.get('assignment_marks')
    exam_marks=request.POST.get('exam_marks')
    subject_id=request.POST.get('subject')


    staff_obj = _logged_in_staff(request)
    student_obj=_assigned_student_or_none(student_admin_id, staff_obj)
    subject_obj=_subject_for_staff_or_none(subject_id, request.user.id)
    if student_obj is None or subject_obj is None:
        messages.error(request, "Invalid student or subject assignment")
        return HttpResponseRedirect(reverse("staff_add_result"))

    try:
        check_exist=StudentResult.objects.filter(subject_id=subject_obj,student_id=student_obj).exists()
        if check_exist:
            result=StudentResult.objects.get(subject_id=subject_obj,student_id=student_obj)
            result.subject_assignment_marks=assignment_marks
            result.subject_exam_marks=exam_marks
            result.save()
            messages.success(request, "Successfully Updated Result")
            return HttpResponseRedirect(reverse("staff_add_result"))
        else:
            result=StudentResult(student_id=student_obj,subject_id=subject_obj,subject_exam_marks=exam_marks,subject_assignment_marks=assignment_marks)
            result.save()
            messages.success(request, "Successfully Added Result")
            return HttpResponseRedirect(reverse("staff_add_result"))
    except:
        messages.error(request, "Failed to Add Result")
        return HttpResponseRedirect(reverse("staff_add_result"))

@csrf_exempt
def fetch_result_student(request):
    subject_id=request.POST.get('subject_id')
    student_id=request.POST.get('student_id')
    staff_obj = _logged_in_staff(request)
    student_obj=_assigned_student_or_none(student_id, staff_obj)
    subject_obj=_subject_for_staff_or_none(subject_id, request.user.id)
    if student_obj is None or subject_obj is None:
        return HttpResponse("False")
    result=StudentResult.objects.filter(student_id=student_obj.id,subject_id=subject_obj.id).exists()
    if result:
        result=StudentResult.objects.get(student_id=student_obj.id,subject_id=subject_obj.id)
        result_data={"exam_marks":result.subject_exam_marks,"assign_marks":result.subject_assignment_marks}
        return HttpResponse(json.dumps(result_data))
    else:
        return HttpResponse("False")

def start_live_classroom(request):
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    session_years=SessionYearModel.object.all()
    return render(request,"staff_template/start_live_classroom.html",{"subjects":subjects,"session_years":session_years})

def start_live_classroom_process(request):
    session_year=request.POST.get("session_year")
    subject=request.POST.get("subject")

    room = create_or_get_active_room(request.user, subject, session_year)
    mark_participant_joined(request.user, room, "STAFF", is_publisher=True)
    return render(
        request,
        "staff_template/live_class_room_start.html",
        {
            "username": request.user.username,
            "password": room.room_pwd,
            "roomid": room.room_name,
            "subject": room.subject.subject_name,
            "session_year": room.session_years,
            "room_pk": room.id,
            "socket_url": settings.LIVE_SIGNALING_URL,
        },
    )


@require_POST
def start_live_classroom_api(request):
    if str(request.user.user_type) != "2":
        return JsonResponse({"ok": False, "error": "Only staff can start class"}, status=403)

    subject = request.POST.get("subject")
    session_year = request.POST.get("session_year")
    if not subject or not session_year:
        return JsonResponse({"ok": False, "error": "subject and session_year are required"}, status=400)

    try:
        room = create_or_get_active_room(request.user, subject, session_year)
        mark_participant_joined(request.user, room, "STAFF", is_publisher=True)
    except ObjectDoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid subject/session"}, status=404)

    token = issue_realtime_token(request.user, room, role="STAFF")
    return JsonResponse(
        {
            "ok": True,
            "room": serialize_room_state(room),
            "room_name": room.room_name,
            "room_password": room.room_pwd,
            "token": token,
            "socket_url": settings.LIVE_SIGNALING_URL,
        }
    )


@require_POST
def end_live_classroom_api(request, room_id):
    if str(request.user.user_type) != "2":
        return JsonResponse({"ok": False, "error": "Only staff can end class"}, status=403)

    try:
        room = OnlineClassRoom.objects.get(id=room_id)
        if room.started_by.admin_id != request.user.id:
            return JsonResponse({"ok": False, "error": "Only class owner can end this room"}, status=403)
        end_room(request.user, room)
    except ObjectDoesNotExist:
        return JsonResponse({"ok": False, "error": "Room not found"}, status=404)

    return JsonResponse({"ok": True, "room": serialize_room_state(room)})


@require_POST
@csrf_exempt
def save_live_class_snapshot_api(request, room_id):
    if str(request.user.user_type) != "2":
        return JsonResponse({"ok": False, "error": "Only staff can save snapshot"}, status=403)

    try:
        room = OnlineClassRoom.objects.get(id=room_id)
        if room.started_by.admin_id != request.user.id:
            return JsonResponse({"ok": False, "error": "Only class owner can save snapshot"}, status=403)
    except ObjectDoesNotExist:
        return JsonResponse({"ok": False, "error": "Room not found"}, status=404)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body"}, status=400)

    snapshot = payload.get("snapshot")
    if snapshot is None:
        return JsonResponse({"ok": False, "error": "snapshot is required"}, status=400)

    room.last_board_snapshot = json.dumps(snapshot)
    room.save(update_fields=["last_board_snapshot"])
    return JsonResponse({"ok": True})


def returnHtmlWidget(request):
    return render(request,"widget.html")
