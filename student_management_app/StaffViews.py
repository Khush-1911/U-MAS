import json
from datetime import date, timedelta

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
from django.utils import timezone

from student_management_app.models import Subjects, SessionYearModel, Students, Attendance, AttendanceReport, \
    LeaveReportStaff, Staffs, FeedBackStaffs, FeedBackStudent, CustomUser, Courses, NotificationStaffs, StudentResult, OnlineClassRoom
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

def _resolve_session_for_date(target_date):
    return SessionYearModel.object.filter(
        session_start_year__lte=target_date,
        session_end_year__gte=target_date,
    ).order_by("id").first()

def _resolve_session_from_students(subject, staff_obj):
    session_ids = list(
        Students.objects.filter(
            course_id=subject.course_id,
            assigned_staff=staff_obj,
        ).values_list("session_year_id", flat=True).distinct()
    )
    if len(session_ids) == 1:
        return SessionYearModel.object.filter(id=session_ids[0]).first()
    return None

def _resolve_fallback_session(attendance_date_obj, subject_model, staff_obj, selected_student_admin_ids=None):
    session_model = _resolve_session_for_date(attendance_date_obj)
    if session_model:
        return session_model

    students_qs = Students.objects.filter(
        assigned_staff=staff_obj,
        course_id=subject_model.course_id,
    )
    if selected_student_admin_ids:
        students_qs = students_qs.filter(admin_id__in=selected_student_admin_ids)

    session_id = students_qs.values_list("session_year_id", flat=True).order_by("session_year_id").first()
    if session_id:
        return SessionYearModel.object.filter(id=session_id).first()

    session_model = SessionYearModel.object.order_by("id").first()
    if session_model:
        return session_model

    year = attendance_date_obj.year
    return SessionYearModel.object.create(
        session_start_year=f"{year}-01-01",
        session_end_year=f"{year}-12-31",
    )

def _daily_attendance_payload_for_staff(staff_user_id, selected_date):
    staff_obj = Staffs.objects.get(admin=staff_user_id)
    students = Students.objects.filter(assigned_staff=staff_obj).select_related("admin").order_by("id")
    reports = AttendanceReport.objects.filter(
        attendance_id__subject_id__staff_id=staff_user_id,
        attendance_id__attendance_date=selected_date,
        student_id__in=students,
    )
    status_map = {}
    for report in reports.select_related("student_id"):
        sid = report.student_id_id
        # If any subject report is absent for the day, treat the student as absent.
        if sid not in status_map:
            status_map[sid] = bool(report.status)
        elif not report.status:
            status_map[sid] = False

    present_students = []
    absent_students = []
    for student in students:
        display_name = (
            student.admin.get_full_name().strip()
            or student.admin.username
            or student.profile_id
        )
        if student.id not in status_map:
            continue
        is_present = status_map[student.id]
        if is_present:
            present_students.append(display_name)
        else:
            absent_students.append(display_name)

    present_students.sort()
    absent_students.sort()
    marked_total = len(present_students) + len(absent_students)

    return {
        "selected_date": selected_date,
        "previous_date": selected_date - timedelta(days=1),
        "next_date": selected_date + timedelta(days=1),
        "present_count": len(present_students),
        "total_students": marked_total,
        "present_students": present_students,
        "absent_students": absent_students,
    }


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

def staff_students_under_me(request):
    staff_obj = _logged_in_staff(request)
    students = (
        Students.objects.filter(assigned_staff=staff_obj)
        .select_related("admin", "course_id", "session_year_id")
        .order_by("id")
    )
    return render(
        request,
        "staff_template/staff_students_under_me.html",
        {"students": students},
    )

def staff_daily_attendance_graph(request):
    selected_date_raw = (request.GET.get("date") or "").strip()

    try:
        selected_date = date.fromisoformat(selected_date_raw) if selected_date_raw else timezone.localdate()
    except ValueError:
        selected_date = timezone.localdate()

    payload = _daily_attendance_payload_for_staff(request.user.id, selected_date)
    context = {
        "selected_date": payload["selected_date"],
        "previous_date": payload["previous_date"],
        "next_date": payload["next_date"],
        "present_count": payload["present_count"],
        "total_students": payload["total_students"],
        "present_students_json": json.dumps(payload["present_students"]),
        "absent_students_json": json.dumps(payload["absent_students"]),
    }
    return render(request, "staff_template/staff_daily_attendance_graph.html", context)

def staff_daily_attendance_graph_data(request):
    selected_date_raw = (request.GET.get("date") or "").strip()
    try:
        selected_date = date.fromisoformat(selected_date_raw) if selected_date_raw else timezone.localdate()
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid date format"}, status=400)

    payload = _daily_attendance_payload_for_staff(request.user.id, selected_date)
    return JsonResponse(
        {
            "ok": True,
            "selected_date": payload["selected_date"].isoformat(),
            "selected_date_display": payload["selected_date"].strftime("%d-%m-%Y"),
            "previous_date": payload["previous_date"].isoformat(),
            "next_date": payload["next_date"].isoformat(),
            "present_count": payload["present_count"],
            "total_students": payload["total_students"],
            "present_students": payload["present_students"],
            "absent_students": payload["absent_students"],
        }
    )

def staff_take_attendance(request):
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    return render(
        request,
        "staff_template/staff_take_attendance.html",
        {
            "subjects": subjects,
            "today_date": timezone.localdate().isoformat(),
        },
    )

@csrf_exempt
def get_students(request):
    subject_id=request.POST.get("subject")
    session_year=request.POST.get("session_year")
    attendance_date_raw = (request.POST.get("attendance_date") or "").strip()

    subject=_subject_for_staff_or_none(subject_id, request.user.id)
    if not subject:
        return JsonResponse({"error": "Invalid subject for this staff"}, status=403)

    session_model = None
    staff_obj = _logged_in_staff(request)
    if attendance_date_raw:
        try:
            date.fromisoformat(attendance_date_raw)
        except ValueError:
            return JsonResponse({"error": "Invalid attendance date"}, status=400)
        students=Students.objects.filter(
            course_id=subject.course_id,
            assigned_staff=staff_obj,
        )
    elif session_year:
        session_model = SessionYearModel.object.filter(id=session_year).first()
        if not session_model:
            session_model = _resolve_session_from_students(subject, staff_obj)
        if not session_model:
            return JsonResponse(json.dumps([]), content_type="application/json", safe=False)
        students=Students.objects.filter(
            course_id=subject.course_id,
            session_year_id=session_model,
            assigned_staff=staff_obj,
        )
    else:
        students=Students.objects.filter(
            course_id=subject.course_id,
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
    subject_model=_subject_for_staff_or_none(subject_id, request.user.id)
    try:
        attendance_date_obj = date.fromisoformat(attendance_date)
    except (TypeError, ValueError):
        return HttpResponse("ERR")

    staff_obj = _logged_in_staff(request)
    json_sstudent=json.loads(student_ids)
    selected_student_admin_ids = [int(stud["id"]) for stud in json_sstudent]
    session_model = _resolve_fallback_session(
        attendance_date_obj,
        subject_model,
        staff_obj,
        selected_student_admin_ids=selected_student_admin_ids,
    ) if subject_model else None
    if not subject_model or not session_model:
        return HttpResponse("ERR")

    try:
        with transaction.atomic():
            attendance, _ = Attendance.objects.get_or_create(
                subject_id=subject_model,
                attendance_date=attendance_date_obj,
                defaults={"session_year_id": session_model},
            )
            if attendance.session_year_id_id != session_model.id:
                attendance.session_year_id = session_model
                attendance.save(update_fields=["session_year_id"])

            for stud in json_sstudent:
                 student=_assigned_student_or_none(stud['id'], staff_obj)
                 if student is None:
                     raise ValueError("Unauthorized student in attendance payload")
                 if student.course_id_id != subject_model.course_id_id:
                     raise ValueError("Student-course mismatch for this subject")
                 status_value = bool(int(stud['status']))
                 attendance_report, created = AttendanceReport.objects.get_or_create(
                     student_id=student,
                     attendance_id=attendance,
                     defaults={"status": status_value},
                 )
                 if not created:
                     attendance_report.status = status_value
                     attendance_report.save(update_fields=["status"])
        return HttpResponse("OK")
    except Exception:
        return HttpResponse("ERR")

def staff_update_attendance(request):
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    return render(request,"staff_template/staff_update_attendance.html",{"subjects":subjects})

@csrf_exempt
def get_attendance_dates(request):
    subject=request.POST.get("subject")
    subject_obj=_subject_for_staff_or_none(subject, request.user.id)
    if not subject_obj:
        return JsonResponse(json.dumps([]),safe=False)

    attendance=Attendance.objects.filter(subject_id=subject_obj).order_by("-attendance_date", "-id")
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
    staff_obj = Staffs.objects.get(admin=request.user.id)
    feedback_data = FeedBackStaffs.objects.filter(staff_id=staff_obj).order_by("-created_at")
    student_feedback_data = (
        FeedBackStudent.objects.filter(staff_id=staff_obj)
        .select_related("student_id__admin", "staff_id__admin")
        .order_by("-created_at")
    )
    return render(
        request,
        "staff_template/staff_feedback.html",
        {
            "feedback_data": feedback_data,
            "student_feedback_data": student_feedback_data,
        },
    )

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


@require_POST
def staff_student_feedback_reply(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    feedback_id = request.POST.get("feedback_id")
    reply_message = (request.POST.get("reply_message") or "").strip()

    if not feedback_id or not reply_message:
        messages.error(request, "Reply message cannot be empty")
        return HttpResponseRedirect(reverse("staff_feedback"))

    feedback = (
        FeedBackStudent.objects.filter(id=feedback_id, staff_id=staff_obj)
        .select_related("student_id__admin")
        .first()
    )
    if feedback is None:
        messages.error(request, "Student feedback not found")
        return HttpResponseRedirect(reverse("staff_feedback"))

    feedback.feedback_reply = reply_message
    feedback.save(update_fields=["feedback_reply"])
    messages.success(
        request,
        f"Reply saved for {feedback.student_id.admin.get_full_name() or feedback.student_id.admin.username}",
    )
    return HttpResponseRedirect(reverse("staff_feedback"))


@require_POST
def staff_student_feedback_forward(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    feedback_id = request.POST.get("feedback_id")

    feedback = (
        FeedBackStudent.objects.filter(id=feedback_id, staff_id=staff_obj)
        .select_related("student_id__admin")
        .first()
    )
    if feedback is None:
        messages.error(request, "Student feedback not found")
        return HttpResponseRedirect(reverse("staff_feedback"))

    if feedback.forwarded_to_hod:
        messages.info(request, "This feedback has already been forwarded to HOD")
        return HttpResponseRedirect(reverse("staff_feedback"))

    feedback.forwarded_to_hod = True
    feedback.forwarded_at = timezone.now()
    feedback.save(update_fields=["forwarded_to_hod", "forwarded_at"])
    messages.success(
        request,
        f"Forwarded {feedback.student_id.admin.get_full_name() or feedback.student_id.admin.username}'s feedback to HOD",
    )
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
    notifications=NotificationStaffs.objects.filter(staff_id=staff.id).order_by("-created_at")
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
