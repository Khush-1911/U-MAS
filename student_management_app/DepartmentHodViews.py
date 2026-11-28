from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Q
from student_management_app.models import (
    CustomUser, Institution, Staffs, Students, Department, HOD, Timetable, ClassModel, SemesterModel,
    Subjects, NotificationStudent, NotificationStaffs, NotificationHOD
)
from student_management_app.notification_utils import (
    create_student_notifications, send_student_notification_emails,
    create_staff_notifications, send_staff_notification_emails,
    create_hod_notifications, send_hod_notification_emails,
)


def _department_for_hod(request):
    try:
        hod_profile = HOD.objects.select_related("department").get(admin=request.user)
    except HOD.DoesNotExist:
        return None
    return hod_profile.department


def _staffs_for_department(department):
    if not department:
        return Staffs.objects.none()
    staff_user_ids = set(Subjects.objects.filter(class_id__department=department).values_list("staff_id", flat=True))
    mentor_staff_ids = set(Students.objects.filter(class_id__department=department, mentor__isnull=False).values_list("mentor_id", flat=True))
    staffs = Staffs.objects.filter(Q(admin_id__in=staff_user_ids) | Q(id__in=mentor_staff_ids)).select_related("admin").distinct().order_by("admin__first_name", "admin__last_name", "id")
    if not staffs.exists():
        if department.institution:
            staffs = Staffs.objects.filter(admin__institution=department.institution).select_related("admin").order_by("admin__first_name", "admin__last_name", "id")
        else:
            staffs = Staffs.objects.select_related("admin").order_by("admin__first_name", "admin__last_name", "id")
    return staffs


def _notification_sender_name(user, department=None):
    full_name = (user.get_full_name() or "").strip() or user.username
    if department:
        return f"{full_name} (HOD - {department.department_name})"
    return f"{full_name} (HOD)"


def department_hod_home(request):
    try:
        hod_profile = HOD.objects.get(admin=request.user)
    except HOD.DoesNotExist:
        messages.error(request, "HOD profile not found.")
        return HttpResponseRedirect(reverse("show_login"))

    department = hod_profile.department
    if not department:
        messages.error(request, "No department assigned to this HOD.")
        return HttpResponseRedirect(reverse("show_login"))

    student_count = Students.objects.filter(class_id__department=department).count()
    staff_count = _staffs_for_department(department).count()
    other_hods_count = HOD.objects.exclude(admin=request.user).count()
    unread_notifications_count = NotificationHOD.objects.filter(hod_id=hod_profile, is_read=False).count()
    recent_notifications = NotificationHOD.objects.filter(hod_id=hod_profile).order_by("-created_at")[:5]

    context = {
        "student_count": student_count,
        "staff_count": staff_count,
        "other_hods_count": other_hods_count,
        "unread_notifications_count": unread_notifications_count,
        "recent_notifications": recent_notifications,
        "department_name": department.department_name
    }
    return render(request, "department_hod_template/home_content.html", context)


def department_hod_upload_timetable(request):
    try:
        hod_profile = HOD.objects.get(admin=request.user)
    except HOD.DoesNotExist:
        messages.error(request, "HOD profile not found.")
        return HttpResponseRedirect(reverse("show_login"))
        
    department = hod_profile.department
    classes = ClassModel.objects.filter(department=department)
    semesters = SemesterModel.objects.all()
    
    return render(request, "department_hod_template/upload_timetable.html", {"classes": classes, "semesters": semesters})


def department_hod_manage_students(request):
    department = _department_for_hod(request)
    if not department:
        messages.error(request, "No department is assigned to this HOD.")
        return HttpResponseRedirect(reverse("department_hod_home"))

    students = (
        Students.objects.filter(class_id__department=department)
        .select_related("admin", "class_id", "semester_id", "mentor__admin")
        .order_by("class_id__class_name", "admin__first_name", "admin__last_name", "id")
    )
    return render(
        request,
        "department_hod_template/manage_students.html",
        {"department": department, "students": students},
    )


def department_hod_manage_staff(request):
    department = _department_for_hod(request)
    if not department:
        messages.error(request, "No department is assigned to this HOD.")
        return HttpResponseRedirect(reverse("department_hod_home"))

    staffs = _staffs_for_department(department).select_related("admin")
    staff_data = []
    for staff in staffs:
        subjects = list(
            Subjects.objects.filter(
                staff_id=staff.admin_id,
                class_id__department=department,
            ).values_list("subject_name", flat=True)
        )
        staff_data.append({
            "staff": staff,
            "subjects": subjects,
        })

    return render(
        request,
        "department_hod_template/manage_staff.html",
        {
            "department": department,
            "staff_data": staff_data,
            "staff_count": len(staff_data),
        },
    )


def department_hod_peer_directory(request):
    department = _department_for_hod(request)
    if not department:
        messages.error(request, "No department is assigned to this HOD.")
        return HttpResponseRedirect(reverse("department_hod_home"))

    other_hods = (
        HOD.objects.exclude(admin=request.user)
        .select_related("admin", "department", "department__institution")
        .order_by("department__department_name", "admin__first_name", "admin__last_name", "id")
    )
    return render(
        request,
        "department_hod_template/peer_directory.html",
        {
            "department": department,
            "other_hods": other_hods,
            "hod_count": other_hods.count(),
        },
    )


def department_hod_upload_timetable_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("department_hod_upload_timetable"))
    
    try:
        hod_profile = HOD.objects.get(admin=request.user)
        department = hod_profile.department
        class_id = request.POST.get("class_id")
        semester_id = request.POST.get("semester_id")
        timetable_file = request.FILES.get("timetable_file")

        if timetable_file and class_id and semester_id:
            class_obj = ClassModel.objects.get(id=class_id, department=department)
            semester_obj = SemesterModel.objects.get(id=semester_id)
            # Save or update timetable
            timetable, created = Timetable.objects.get_or_create(
                department=department,
                class_id=class_obj,
                semester=semester_obj
            )
            timetable.timetable_file = timetable_file
            timetable.save()
            messages.success(request, "Timetable Successfully Uploaded")
        else:
            messages.error(request, "Please provide class, semester, and a valid file.")
    except Exception as e:
        messages.error(request, f"Failed to upload timetable: {str(e)}")
        
    return HttpResponseRedirect(reverse("department_hod_upload_timetable"))


def department_hod_send_notification(request):
    department = _department_for_hod(request)
    if not department:
        messages.error(request, "No department is assigned to this HOD.")
        return HttpResponseRedirect(reverse("department_hod_home"))

    students = (
        Students.objects.filter(class_id__department=department)
        .select_related("admin", "class_id")
        .order_by("class_id__class_name", "admin__first_name", "admin__last_name", "id")
    )
    staffs = _staffs_for_department(department)
    other_hods = (
        HOD.objects.exclude(admin=request.user)
        .select_related("admin", "department")
        .order_by("department__department_name", "admin__first_name", "admin__last_name", "id")
    )
    classes = ClassModel.objects.filter(department=department).order_by("class_name")

    context = {
        "department": department,
        "students": students,
        "staffs": staffs,
        "other_hods": other_hods,
        "classes": classes,
        "student_count": students.count(),
        "staff_count": staffs.count(),
        "other_hods_count": other_hods.count(),
    }
    return render(request, "department_hod_template/send_notification.html", context)


def department_hod_send_notification_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("department_hod_send_notification"))

    department = _department_for_hod(request)
    if not department:
        messages.error(request, "No department is assigned to this HOD.")
        return HttpResponseRedirect(reverse("department_hod_home"))

    title = (request.POST.get("title") or "").strip()
    message = (request.POST.get("message") or "").strip()
    target_group = (request.POST.get("target_group") or "").strip().lower()
    selected_class_id = (request.POST.get("class_id") or "").strip()
    selected_staff_ids = request.POST.getlist("staff_ids")
    selected_student_ids = request.POST.getlist("student_ids")
    selected_hod_ids = request.POST.getlist("hod_ids")

    if not title:
        messages.error(request, "Notification title is required.")
        return HttpResponseRedirect(reverse("department_hod_send_notification"))

    if not message:
        messages.error(request, "Notification body is required.")
        return HttpResponseRedirect(reverse("department_hod_send_notification"))

    valid_targets = {"staff", "student", "department_all", "other_hods", "all"}
    if target_group not in valid_targets:
        messages.error(request, "Please select whom to notify.")
        return HttpResponseRedirect(reverse("department_hod_send_notification"))

    sender_name = _notification_sender_name(request.user, department)

    staff_recipients = []
    student_recipients = []
    hod_recipients = []

    # Handle Staff
    if target_group in {"staff", "department_all", "all"}:
        dept_staffs = _staffs_for_department(department)
        if selected_staff_ids and "all" not in selected_staff_ids:
            staff_recipients = list(dept_staffs.filter(id__in=selected_staff_ids))
        else:
            staff_recipients = list(dept_staffs)

    # Handle Students
    if target_group in {"student", "department_all", "all"}:
        dept_students = Students.objects.filter(class_id__department=department).select_related("admin", "class_id")
        if selected_class_id and selected_class_id != "all":
            dept_students = dept_students.filter(class_id_id=selected_class_id)
        if selected_student_ids and "all" not in selected_student_ids:
            # Note: selected_student_ids can be student.id or student.admin.id
            student_recipients = list(dept_students.filter(Q(id__in=selected_student_ids) | Q(admin_id__in=selected_student_ids)))
        else:
            student_recipients = list(dept_students)

    # Handle Other HODs
    if target_group in {"other_hods", "all"}:
        other_hods_qs = HOD.objects.exclude(admin=request.user).select_related("admin", "department")
        if selected_hod_ids and "all" not in selected_hod_ids:
            hod_recipients = list(other_hods_qs.filter(id__in=selected_hod_ids))
        else:
            hod_recipients = list(other_hods_qs)

    total_recipients = len(staff_recipients) + len(student_recipients) + len(hod_recipients)
    if total_recipients == 0:
        messages.error(request, "No recipients found for the selected option.")
        return HttpResponseRedirect(reverse("department_hod_send_notification"))

    if staff_recipients:
        create_staff_notifications(staff_recipients, sender_name=sender_name, title=title, message=message)
        send_staff_notification_emails(staff_recipients, sender_name=sender_name, title=title, message=message)

    if student_recipients:
        create_student_notifications(student_recipients, sender_name=sender_name, title=title, message=message)
        send_student_notification_emails(student_recipients, sender_name=sender_name, title=title, message=message)

    if hod_recipients:
        create_hod_notifications(hod_recipients, sender_name=sender_name, title=title, message=message)
        send_hod_notification_emails(hod_recipients, sender_name=sender_name, title=title, message=message)

    messages.success(
        request,
        f"Notification successfully broadcasted to {len(staff_recipients)} staff, "
        f"{len(student_recipients)} students, and {len(hod_recipients)} other HODs.",
    )
    return HttpResponseRedirect(reverse("department_hod_send_notification"))


def department_hod_notifications(request):
    try:
        hod_profile = HOD.objects.get(admin=request.user)
    except HOD.DoesNotExist:
        messages.error(request, "HOD profile not found.")
        return HttpResponseRedirect(reverse("show_login"))

    notifications = NotificationHOD.objects.filter(hod_id=hod_profile).order_by("is_read", "-created_at")
    unread_count = notifications.filter(is_read=False).count()
    read_count = notifications.filter(is_read=True).count()

    return render(
        request,
        "department_hod_template/all_notification.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
            "read_count": read_count,
            "total_count": notifications.count(),
        },
    )


def department_hod_notification_mark_read(request, notification_id):
    try:
        hod_profile = HOD.objects.get(admin=request.user)
    except HOD.DoesNotExist:
        return JsonResponse({"ok": False, "error": "HOD profile not found"}, status=403)

    if notification_id == 0:
        # Mark all as read
        NotificationHOD.objects.filter(hod_id=hod_profile, is_read=False).update(is_read=True)
        unread_count = 0
    else:
        notification = get_object_or_404(NotificationHOD, id=notification_id, hod_id=hod_profile)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        unread_count = NotificationHOD.objects.filter(hod_id=hod_profile, is_read=False).count()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.method == "POST":
        return JsonResponse({"ok": True, "unread_count": unread_count})

    return HttpResponseRedirect(reverse("department_hod_notifications"))
