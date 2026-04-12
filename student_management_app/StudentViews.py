import datetime
import json

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from student_management_app.models import Students, Courses, Subjects, CustomUser, Attendance, AttendanceReport, \
    LeaveReportStudent, FeedBackStudent, NotificationStudent, StudentResult, OnlineClassRoom, SessionYearModel
from student_management_app.services.live_class_service import (
    LiveClassError,
    issue_realtime_token,
    mark_participant_joined,
    validate_student_can_join,
)


def student_home(request):
    student_obj=Students.objects.get(admin=request.user.id)
    attendance_total=AttendanceReport.objects.filter(student_id=student_obj).count()
    attendance_present=AttendanceReport.objects.filter(student_id=student_obj,status=True).count()
    attendance_absent=AttendanceReport.objects.filter(student_id=student_obj,status=False).count()
    course=Courses.objects.get(id=student_obj.course_id.id)
    subjects=Subjects.objects.filter(course_id=course).count()
    subjects_data=Subjects.objects.filter(course_id=course)
    if student_obj.assigned_staff_id:
        subjects_data = subjects_data.filter(staff_id=student_obj.assigned_staff.admin_id)
    session_obj=SessionYearModel.object.get(id=student_obj.session_year_id.id)
    class_room=OnlineClassRoom.objects.filter(subject__in=subjects_data,is_active=True,session_years=session_obj)

    subject_name=[]
    data_present=[]
    data_absent=[]
    subject_data=Subjects.objects.filter(course_id=student_obj.course_id)
    for subject in subject_data:
        attendance=Attendance.objects.filter(subject_id=subject.id)
        attendance_present_count=AttendanceReport.objects.filter(attendance_id__in=attendance,status=True,student_id=student_obj.id).count()
        attendance_absent_count=AttendanceReport.objects.filter(attendance_id__in=attendance,status=False,student_id=student_obj.id).count()
        subject_name.append(subject.subject_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)

    return render(request,"student_template/student_home_template.html",{"total_attendance":attendance_total,"attendance_absent":attendance_absent,"attendance_present":attendance_present,"subjects":subjects,"data_name":subject_name,"data1":data_present,"data2":data_absent,"class_room":class_room})

def join_class_room(request,subject_id,session_year_id):
    session_year_obj=SessionYearModel.object.get(id=session_year_id)
    subjects=Subjects.objects.filter(id=subject_id)
    if subjects.exists():
        session=SessionYearModel.object.filter(id=session_year_obj.id)
        if session.exists():
            subject_obj=Subjects.objects.get(id=subject_id)
            course=Courses.objects.get(id=subject_obj.course_id.id)
            student_obj = Students.objects.filter(admin=request.user.id,course_id=course.id).first()
            check_course=student_obj is not None
            if student_obj and student_obj.assigned_staff_id and subject_obj.staff_id_id != student_obj.assigned_staff.admin_id:
                return HttpResponse("This Subject is Not For You")
            if check_course:
                session_check=Students.objects.filter(admin=request.user.id,session_year_id=session_year_obj.id)
                if session_check.exists():
                    onlineclass_qs = OnlineClassRoom.objects.filter(
                        session_years=session_year_id,
                        subject=subject_id,
                        is_active=True,
                        status="ACTIVE",
                    )
                    if not onlineclass_qs.exists():
                        return HttpResponse("This Online Session Has Ended")
                    onlineclass = onlineclass_qs.first()
                    return render(
                        request,
                        "student_template/join_class_room_start.html",
                        {
                            "username": request.user.username,
                            "password": onlineclass.room_pwd,
                            "roomid": onlineclass.room_name,
                            "room_pk": onlineclass.id,
                            "socket_url": settings.LIVE_SIGNALING_URL,
                        },
                    )

                else:
                    return HttpResponse("This Online Session is Not For You")
            else:
                return HttpResponse("This Subject is Not For You")
        else:
            return HttpResponse("Session Year Not Found")
    else:
        return HttpResponse("Subject Not Found")


def student_view_attendance(request):
    student=Students.objects.get(admin=request.user.id)
    course=student.course_id
    subjects=Subjects.objects.filter(course_id=course)
    return render(request,"student_template/student_view_attendance.html",{"subjects":subjects})

def student_view_attendance_post(request):
    subject_id = request.POST.get("subject")
    start_date = (request.POST.get("start_date") or "").strip()
    end_date = (request.POST.get("end_date") or "").strip()

    if not start_date or not end_date:
        messages.error(request, "Please select both start date and end date.")
        return HttpResponseRedirect(reverse("student_view_attendance"))

    try:
        start_data_parse = datetime.date.fromisoformat(start_date)
        end_data_parse = datetime.date.fromisoformat(end_date)
    except ValueError:
        messages.error(request, "Invalid date format. Please choose valid dates.")
        return HttpResponseRedirect(reverse("student_view_attendance"))

    if start_data_parse > end_data_parse:
        messages.error(request, "Start date cannot be after end date.")
        return HttpResponseRedirect(reverse("student_view_attendance"))

    subject_obj = Subjects.objects.filter(id=subject_id).first()
    if not subject_obj:
        messages.error(request, "Selected subject was not found.")
        return HttpResponseRedirect(reverse("student_view_attendance"))

    user_object = CustomUser.objects.get(id=request.user.id)
    stud_obj = Students.objects.get(admin=user_object)
    if subject_obj.course_id_id != stud_obj.course_id_id:
        messages.error(request, "You are not allowed to view attendance for this subject.")
        return HttpResponseRedirect(reverse("student_view_attendance"))

    attendance = Attendance.objects.filter(
        attendance_date__range=(start_data_parse, end_data_parse),
        subject_id=subject_obj,
    )
    attendance_reports = AttendanceReport.objects.filter(attendance_id__in=attendance, student_id=stud_obj)
    return render(request, "student_template/student_attendance_data.html", {"attendance_reports":attendance_reports})

def student_apply_leave(request):
    staff_obj = Students.objects.get(admin=request.user.id)
    leave_data=LeaveReportStudent.objects.filter(student_id=staff_obj)
    return render(request,"student_template/student_apply_leave.html",{"leave_data":leave_data})

def student_apply_leave_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("student_apply_leave"))
    else:
        leave_date=request.POST.get("leave_date")
        leave_msg=request.POST.get("leave_msg")

        student_obj=Students.objects.get(admin=request.user.id)
        try:
            leave_report=LeaveReportStudent(student_id=student_obj,leave_date=leave_date,leave_message=leave_msg,leave_status=0)
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))
        except:
            messages.error(request, "Failed To Apply for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))


def student_feedback(request):
    student_obj = Students.objects.select_related("assigned_staff__admin").get(admin=request.user.id)
    feedback_data = (
        FeedBackStudent.objects.filter(student_id=student_obj)
        .select_related("staff_id__admin")
        .order_by("-created_at")
    )
    return render(
        request,
        "student_template/student_feedback.html",
        {
            "feedback_data": feedback_data,
            "assigned_staff": student_obj.assigned_staff,
        },
    )

def student_feedback_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("student_feedback"))
    else:
        feedback_msg = (request.POST.get("feedback_msg") or "").strip()

        student_obj = Students.objects.select_related("assigned_staff").get(admin=request.user.id)
        if not feedback_msg:
            messages.error(request, "Feedback message cannot be empty")
            return HttpResponseRedirect(reverse("student_feedback"))

        if student_obj.assigned_staff is None:
            messages.error(request, "No faculty is assigned to you yet. Please contact HOD.")
            return HttpResponseRedirect(reverse("student_feedback"))

        try:
            feedback = FeedBackStudent(
                student_id=student_obj,
                staff_id=student_obj.assigned_staff,
                feedback=feedback_msg,
                feedback_reply="",
                hod_reply="",
            )
            feedback.save()
            messages.success(request, "Successfully sent feedback to your assigned faculty")
            return HttpResponseRedirect(reverse("student_feedback"))
        except:
            messages.error(request, "Failed To Send Feedback")
            return HttpResponseRedirect(reverse("student_feedback"))

def student_profile(request):
    user=CustomUser.objects.get(id=request.user.id)
    student=Students.objects.get(admin=user)
    return render(request,"student_template/student_profile.html",{"user":user,"student":student})

def student_profile_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("student_profile"))
    else:
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        password=request.POST.get("password")
        address=request.POST.get("address")
        try:
            customuser=CustomUser.objects.get(id=request.user.id)
            customuser.first_name=first_name
            customuser.last_name=last_name
            if password!=None and password!="":
                customuser.set_password(password)
            customuser.save()

            student=Students.objects.get(admin=customuser)
            student.address=address
            student.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("student_profile"))
        except:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("student_profile"))

@csrf_exempt
def student_fcmtoken_save(request):
    token=request.POST.get("token")
    try:
        student=Students.objects.get(admin=request.user.id)
        student.fcm_token=token
        student.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")

def student_all_notification(request):
    student=Students.objects.get(admin=request.user.id)
    notifications=NotificationStudent.objects.filter(student_id=student.id).order_by("is_read", "-created_at")
    return render(request,"student_template/all_notification.html",{"notifications":notifications})


@require_POST
def student_notification_mark_read(request, notification_id):
    student = Students.objects.get(admin=request.user.id)
    updated = NotificationStudent.objects.filter(
        id=notification_id,
        student_id=student.id,
        is_read=False,
    ).update(is_read=True)
    unread_count = NotificationStudent.objects.filter(
        student_id=student.id,
        is_read=False,
    ).count()
    return JsonResponse({"ok": True, "marked_read": bool(updated), "unread_count": unread_count})

def student_view_result(request):
    student=Students.objects.get(admin=request.user.id)
    studentresult=StudentResult.objects.filter(student_id=student.id)
    return render(request,"student_template/student_result.html",{"studentresult":studentresult})


@require_POST
@csrf_exempt
def live_class_join_token_api(request, room_id):
    if str(request.user.user_type) != "3":
        return JsonResponse({"ok": False, "error": "Only students can join"}, status=403)

    try:
        room = OnlineClassRoom.objects.get(id=room_id)
        validate_student_can_join(request.user, room)
    except ObjectDoesNotExist:
        return JsonResponse({"ok": False, "error": "Room not found"}, status=404)
    except LiveClassError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=403)

    token = issue_realtime_token(request.user, room, role="STUDENT")
    mark_participant_joined(request.user, room, "STUDENT", is_publisher=False)
    return JsonResponse(
        {
            "ok": True,
            "token": token,
            "room_id": room.id,
            "room_name": room.room_name,
            "socket_url": settings.LIVE_SIGNALING_URL,
            "snapshot": json.loads(room.last_board_snapshot) if room.last_board_snapshot else None,
        }
    )
