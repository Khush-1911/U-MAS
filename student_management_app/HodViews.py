import json

import requests
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from student_management_app.forms import AddStudentForm, EditStudentForm
from student_management_app.models import CustomUser, Staffs, Department, Subjects, Students, SemesterModel, ClassModel, \
    FeedBackStudent, FeedBackStaffs, LeaveReportStudent, LeaveReportStaff, Attendance, AttendanceReport, \
    NotificationStudent, NotificationStaffs
from student_management_app.notification_utils import (
    create_student_notifications,
    send_student_notification_emails,
)


def _normalize_email(value):
    return (value or "").strip().lower()


def _credentials_error(email, exclude_user_id=None):
    email = _normalize_email(email)

    if not email:
        return "Email is required"

    email_qs = CustomUser.objects.filter(email__iexact=email)
    if exclude_user_id:
        email_qs = email_qs.exclude(id=exclude_user_id)

    if email_qs.exists():
        return "Email already exists"
    return None


def _notification_sender_name(user):
    if not user:
        return "HOD"

    full_name = user.get_full_name().strip()
    return full_name or user.username or "HOD"


IMPORTED_STUDENT_USERNAMES = [
    "khush",
    "dhrumil",
    "harmin",
    "keval",
    "apurv",
    "devam",
    "yuvraj",
    "avi",
    "rushi",
    "nirdosh",
    "subham",
    "oum",
]


def _normalize_department_name(value):
    return " ".join((value or "").strip().lower().split())


def _contains_word_sequence(full_name, sub_name):
    full_tokens = _normalize_department_name(full_name).split()
    sub_tokens = _normalize_department_name(sub_name).split()
    if not full_tokens or not sub_tokens or len(sub_tokens) > len(full_tokens):
        return False
    for idx in range(len(full_tokens) - len(sub_tokens) + 1):
        if full_tokens[idx : idx + len(sub_tokens)] == sub_tokens:
            return True
    return False


def _department_name_conflict(department_name, exclude_department_id=None):
    normalized_new = _normalize_department_name(department_name)
    if not normalized_new:
        return "Department name is required"

    existing_departments = Department.objects.all()
    if exclude_department_id:
        existing_departments = existing_departments.exclude(id=exclude_department_id)

    for existing in existing_departments:
        normalized_existing = _normalize_department_name(existing.department_name)
        if (
            normalized_new == normalized_existing
            or _contains_word_sequence(normalized_existing, normalized_new)
            or _contains_word_sequence(normalized_new, normalized_existing)
        ):
            return (
                f'Department "{existing.department_name}" already exists or overlaps '
                "with this name. Please use a distinct name."
            )
    return None


def admin_home(request):
    institution = request.user.institution
    if not institution:
        return render(request, "hod_template/home_content.html", {"error": "No institution assigned"})

    student_count1 = Students.objects.filter(admin__institution=institution).count()
    staff_count = Staffs.objects.filter(admin__institution=institution).count()
    subject_count = Subjects.objects.filter(class_id__department__institution=institution).count()
    department_count = Department.objects.filter(institution=institution).count()

    department_all = Department.objects.filter(institution=institution)
    department_name_list = []
    subject_count_list = []
    student_count_list_in_department = []
    for department in department_all:
        subjects = Subjects.objects.filter(class_id__department_id=department.id).count()
        students = Students.objects.filter(class_id__department_id=department.id).count()
        department_name_list.append(department.department_name)
        subject_count_list.append(subjects)
        student_count_list_in_department.append(students)

    subjects_all = Subjects.objects.filter(class_id__department__institution=institution)
    subject_list = []
    student_count_list_in_subject = []
    for subject in subjects_all:
        student_count = Students.objects.filter(class_id=subject.class_id).count()
        subject_list.append(subject.subject_name)
        student_count_list_in_subject.append(student_count)

    staffs = Staffs.objects.filter(admin__institution=institution)
    attendance_present_list_staff = []
    attendance_absent_list_staff = []
    staff_name_list = []
    for staff in staffs:
        subject_ids = Subjects.objects.filter(staff_id=staff.admin.id)
        attendance = Attendance.objects.filter(subject_id__in=subject_ids).count()
        leaves = LeaveReportStaff.objects.filter(staff_id=staff.id, leave_status=1).count()
        attendance_present_list_staff.append(attendance)
        attendance_absent_list_staff.append(leaves)
        staff_name_list.append(staff.admin.username)

    students_all = Students.objects.filter(admin__institution=institution)
    attendance_present_list_student = []
    attendance_absent_list_student = []
    student_name_list = []
    for student in students_all:
        attendance = AttendanceReport.objects.filter(student_id=student.id, status=True).count()
        absent = AttendanceReport.objects.filter(student_id=student.id, status=False).count()
        leaves = LeaveReportStudent.objects.filter(student_id=student.id, leave_status=1).count()
        attendance_present_list_student.append(attendance)
        attendance_absent_list_student.append(leaves + absent)
        student_name_list.append(student.admin.username)

    return render(request, "hod_template/home_content.html", {
        "student_count": student_count1,
        "staff_count": staff_count,
        "subject_count": subject_count,
        "department_count": department_count,
        "department_name_list": department_name_list,
        "subject_count_list": subject_count_list,
        "student_count_list_in_department": student_count_list_in_department,
        "student_count_list_in_subject": student_count_list_in_subject,
        "subject_list": subject_list,
        "staff_name_list": staff_name_list,
        "attendance_present_list_staff": attendance_present_list_staff,
        "attendance_absent_list_staff": attendance_absent_list_staff,
        "student_name_list": student_name_list,
        "attendance_present_list_student": attendance_present_list_student,
        "attendance_absent_list_student": attendance_absent_list_student
    })

def add_staff(request):
    students = (
        Students.objects.select_related("admin", "mentor")
        .order_by("admin__first_name", "admin__last_name", "admin__username")
    )
    return render(
        request,
        "hod_template/add_staff_template.html",
        {"students": students},
    )

def add_staff_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        first_name=request.POST.get("first_name", "").strip()
        last_name=request.POST.get("last_name", "").strip()
        if not all([first_name, last_name, email, password, address]):
            messages.error(request,"All fields are required")
            return HttpResponseRedirect(reverse("add_staff"))

        error = _credentials_error(email)
        if error:
            messages.error(request, error)
            return HttpResponseRedirect(reverse("add_staff"))

        try:
            with transaction.atomic():
                user=CustomUser.objects.create_user(
                    username=email,
                    password=password,
                    email=email,
                    notification_email=notification_email,
                    last_name=last_name,
                    first_name=first_name,
                    user_type=2,
                )
                user.staffs.address=address
                user.staffs.save(update_fields=["address"])
                if selected_student_ids:
                    Students.objects.filter(admin_id__in=selected_student_ids).update(
                        mentor=user.staffs
                    )
            messages.success(request,"Successfully Added Staff")
            return HttpResponseRedirect(reverse("add_staff"))
        except IntegrityError:
            messages.error(request,"Email already exists")
            return HttpResponseRedirect(reverse("add_staff"))
        except Exception:
            messages.error(request,"Failed to Add Staff")
            return HttpResponseRedirect(reverse("add_staff"))

def add_department(request):
    return render(request,"hod_template/add_department_template.html")

def add_department_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        department = (request.POST.get("department") or "").strip()
        conflict_error = _department_name_conflict(department)
        if conflict_error:
            messages.error(request, conflict_error)
            return HttpResponseRedirect(reverse("add_department"))
        try:
            department_model=Department(department_name=department)
            department_model.save()
            messages.success(request,"Successfully Added Department")
            return HttpResponseRedirect(reverse("add_department"))
        except Exception as e:
            print(e)
            messages.error(request,"Failed To Add Department")
            return HttpResponseRedirect(reverse("add_department"))

def add_student(request):
    if not Staffs.objects.exists():
        messages.error(request, "Add at least one staff before creating students")
    form=AddStudentForm()
    return render(request,"hod_template/add_student_template.html",{"form":form})

def add_student_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        form=AddStudentForm(request.POST,request.FILES)
        if form.is_valid():
            first_name=form.cleaned_data["first_name"]
            last_name=form.cleaned_data["last_name"]
            email=_normalize_email(form.cleaned_data["email"])
            notification_email = _normalize_email(form.cleaned_data["notification_email"]) or email
            password=form.cleaned_data["password"]
            address=form.cleaned_data["address"]
            semester_id=form.cleaned_data["semester_id"]
            class_id=form.cleaned_data["class_id"]
            sex=form.cleaned_data["sex"]
            mentor_id=form.cleaned_data["mentor"]

            if not password:
                messages.error(request, "Password is required")
                return HttpResponseRedirect(reverse("add_student"))

            error = _credentials_error(email)
            if error:
                messages.error(request, error)
                return HttpResponseRedirect(reverse("add_student"))

            try:
                with transaction.atomic():
                    class_obj=ClassModel.objects.get(id=class_id)
                    semester=SemesterModel.object.get(id=semester_id)
                    mentor=Staffs.objects.get(id=mentor_id)

                    user=CustomUser.objects.create_user(
                        username=email,
                        password=password,
                        email=email,
                        notification_email=notification_email,
                        last_name=last_name,
                        first_name=first_name,
                        user_type=3,
                    )
                    user.students.address=address
                    user.students.class_id=class_obj
                    user.students.semester_id=semester
                    user.students.gender=sex
                    user.students.mentor=mentor
                    user.students.save()
                messages.success(request,"Successfully Added Student")
                return HttpResponseRedirect(reverse("add_student"))
            except (Department.DoesNotExist, SemesterModel.DoesNotExist, Staffs.DoesNotExist):
                messages.error(request,"Invalid department, semester, or assigned staff")
                return HttpResponseRedirect(reverse("add_student"))
            except IntegrityError:
                messages.error(request,"Email already exists")
                return HttpResponseRedirect(reverse("add_student"))
            except Exception:
                messages.error(request,"Failed to Add Student")
                return HttpResponseRedirect(reverse("add_student"))
        else:
            form=AddStudentForm(request.POST)
            return render(request, "hod_template/add_student_template.html", {"form": form})


def add_subject(request):
    classes=ClassModel.objects.all()
    staffs=CustomUser.objects.filter(user_type=2)
    return render(request,"hod_template/add_subject_template.html",{"staffs":staffs,"classes":classes})

def add_subject_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_name=request.POST.get("subject_name")
        class_id=request.POST.get("class")
        class_obj=ClassModel.objects.get(id=class_id)
        staff_id=request.POST.get("staff")
        staff=CustomUser.objects.get(id=staff_id)

        try:
            subject=Subjects(subject_name=subject_name,class_id=class_obj,staff_id=staff)
            subject.save()
            messages.success(request,"Successfully Added Subject")
            return HttpResponseRedirect(reverse("add_subject"))
        except:
            messages.error(request,"Failed to Add Subject")
            return HttpResponseRedirect(reverse("add_subject"))


def manage_staff(request):
    staffs=Staffs.objects.all()
    return render(request,"hod_template/manage_staff_template.html",{"staffs":staffs})

def manage_student(request):
    students=Students.objects.all()
    return render(request,"hod_template/manage_student_template.html",{"students":students})

def manage_department(request):
    departments=Department.objects.all()
    return render(request,"hod_template/manage_department_template.html",{"departments":departments})

def manage_subject(request):
    subjects=Subjects.objects.all()
    return render(request,"hod_template/manage_subject_template.html",{"subjects":subjects})

def delete_staff(request,staff_id):
    try:
        user=CustomUser.objects.get(id=staff_id)
        user.delete()
        messages.success(request,"Successfully Deleted Staff")
    except:
        messages.error(request,"Failed to Delete Staff")
    return HttpResponseRedirect(reverse("manage_staff"))

def delete_student(request,student_id):
    try:
        user=CustomUser.objects.get(id=student_id)
        user.delete()
        messages.success(request,"Successfully Deleted Student")
    except:
        messages.error(request,"Failed to Delete Student")
    return HttpResponseRedirect(reverse("manage_student"))

def delete_subject(request,subject_id):
    try:
        subject=Subjects.objects.get(id=subject_id)
        subject.delete()
        messages.success(request,"Successfully Deleted Subject")
    except:
        messages.error(request,"Failed to Delete Subject")
    return HttpResponseRedirect(reverse("manage_subject"))

def delete_department(request,department_id):
    try:
        department=Department.objects.get(id=department_id)
        department.delete()
        messages.success(request,"Successfully Deleted Department")
    except:
        messages.error(request,"Failed to Delete Department")
    return HttpResponseRedirect(reverse("manage_department"))

def edit_staff(request,staff_id):
    staff=Staffs.objects.get(admin=staff_id)
    students = (
        Students.objects.select_related("admin", "mentor")
        .order_by("admin__first_name", "admin__last_name", "admin__username")
    )
    selected_student_ids = set(
        Students.objects.filter(mentor=staff).values_list("admin_id", flat=True)
    )
    return render(
        request,
        "hod_template/edit_staff_template.html",
        {
            "staff": staff,
            "id": staff_id,
            "students": students,
            "selected_student_ids": selected_student_ids,
            "institutions": Institution.objects.all(),
            "roles": CustomUser.user_type_data,
        },
    )

def edit_staff_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        staff_id=request.POST.get("staff_id")
        first_name=request.POST.get("first_name", "").strip()
        last_name=request.POST.get("last_name", "").strip()
        email=_normalize_email(request.POST.get("email"))
        notification_email = _normalize_email(request.POST.get("notification_email")) or email
        address=request.POST.get("address", "").strip()
            if student_id.isdigit()
        }
        role_id = request.POST.get("role")
        institution_id = request.POST.get("institution")

        if not all([first_name, last_name, email, address]):
            messages.error(request,"All fields are required")
            return HttpResponseRedirect(reverse("edit_staff",kwargs={"staff_id":staff_id}))

        error = _credentials_error(email, exclude_user_id=staff_id)
        if error:
            messages.error(request, error)
            return HttpResponseRedirect(reverse("edit_staff",kwargs={"staff_id":staff_id}))

        try:
            with transaction.atomic():
                user=CustomUser.objects.get(id=staff_id)
                user.first_name=first_name
                user.last_name=last_name
                user.email=email
                user.notification_email=notification_email
                user.username=email
                user.user_type = role_id
                if institution_id:
                    user.institution = Institution.objects.get(id=institution_id)
                user.save()

                # Profile creation logic
                if role_id == "3" and not hasattr(user, 'students'):
                    Students.objects.create(admin=user, address="", gender="", mentor=None)
                elif role_id == "7" and not hasattr(user, 'hod'):
                    HOD.objects.create(admin=user)

                staff_model=Staffs.objects.get(admin=staff_id)
                staff_model.address=address
                staff_model.save()

                Students.objects.filter(mentor=staff_model).exclude(
                    admin_id__in=selected_student_ids
                ).update(mentor=None)
                if selected_student_ids:
                    Students.objects.filter(admin_id__in=selected_student_ids).update(
                        mentor=staff_model
                    )
            messages.success(request,"Successfully Edited Staff")
            return HttpResponseRedirect(reverse("edit_staff",kwargs={"staff_id":staff_id}))
        except IntegrityError:
            messages.error(request,"Email already exists")
            return HttpResponseRedirect(reverse("edit_staff",kwargs={"staff_id":staff_id}))
        except Exception:
            messages.error(request,"Failed to Edit Staff")
            return HttpResponseRedirect(reverse("edit_staff",kwargs={"staff_id":staff_id}))

def edit_student(request,student_id):
    request.session['student_id']=student_id
    student=Students.objects.get(admin=student_id)
    form=EditStudentForm()
    form.fields['email'].initial=student.admin.email
    form.fields['notification_email'].initial=student.admin.notification_email
    form.fields['first_name'].initial=student.admin.first_name
    form.fields['last_name'].initial=student.admin.last_name
    form.fields['username'].initial=student.admin.username
    form.fields['address'].initial=student.address
    form.fields['class_id'].initial=student.class_id.id if student.class_id else None
    form.fields['sex'].initial=student.gender
    form.fields['semester_id'].initial=student.semester_id.id
    form.fields['mentor'].initial=student.mentor_id
    return render(request,"hod_template/edit_student_template.html",{"form":form,"id":student_id,"username":student.admin.username})

def edit_student_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        student_id=request.session.get("student_id")
        if student_id==None:
            return HttpResponseRedirect(reverse("manage_student"))

        form=EditStudentForm(request.POST,request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            email = _normalize_email(form.cleaned_data["email"])
            notification_email = _normalize_email(form.cleaned_data["notification_email"]) or email
            address = form.cleaned_data["address"]
            semester_id=form.cleaned_data["semester_id"]
            class_id = form.cleaned_data["class_id"]
            sex = form.cleaned_data["sex"]
            mentor_id = form.cleaned_data["mentor"]

            error = _credentials_error(email, exclude_user_id=student_id)
            if error:
                messages.error(request, error)
                return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))

            try:
                with transaction.atomic():
                    user=CustomUser.objects.get(id=student_id)
                    user.first_name=first_name
                    user.last_name=last_name
                    user.username=email
                    user.email=email
                    user.notification_email=notification_email
                    user.user_type = form.cleaned_data["user_type"]
                    user.institution = Institution.objects.get(id=form.cleaned_data["institution"])
                    user.save()

                    # Profile creation logic
                    if user.user_type == "2" and not hasattr(user, 'staffs'):
                        Staffs.objects.create(admin=user, address="")
                    elif user.user_type == "7" and not hasattr(user, 'hod'):
                        HOD.objects.create(admin=user)

                    student=Students.objects.get(admin=student_id)
                    student.address=address
                    semester = SemesterModel.object.get(id=semester_id)
                    student.semester_id = semester
                    student.gender=sex
                    class_obj=ClassModel.objects.get(id=class_id)
                    mentor=Staffs.objects.get(id=mentor_id)
                    student.class_id=class_obj
                    student.mentor=mentor
                    student.save()
                del request.session['student_id']
                messages.success(request,"Successfully Edited Student")
                return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))
            except (ClassModel.DoesNotExist, SemesterModel.DoesNotExist, Staffs.DoesNotExist):
                messages.error(request,"Invalid class, semester, or assigned staff")
                return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))
            except IntegrityError:
                messages.error(request,"Email already exists")
                return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))
            except Exception:
                messages.error(request,"Failed to Edit Student")
                return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))
        else:
            form=EditStudentForm(request.POST)
            student=Students.objects.get(admin=student_id)
            return render(request,"hod_template/edit_student_template.html",{"form":form,"id":student_id,"username":student.admin.username})

def edit_subject(request,subject_id):
    subject=Subjects.objects.get(id=subject_id)
    classes=ClassModel.objects.all()
    staffs=CustomUser.objects.filter(user_type=2)
    return render(request,"hod_template/edit_subject_template.html",{"subject":subject,"staffs":staffs,"classes":classes,"id":subject_id})

def edit_subject_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_id=request.POST.get("subject_id")
        subject_name=request.POST.get("subject_name")
        staff_id=request.POST.get("staff")
        class_id=request.POST.get("class")

        try:
            subject=Subjects.objects.get(id=subject_id)
            subject.subject_name=subject_name
            staff=CustomUser.objects.get(id=staff_id)
            subject.staff_id=staff
            class_obj=ClassModel.objects.get(id=class_id)
            subject.class_id=class_obj
            subject.save()

            messages.success(request,"Successfully Edited Subject")
            return HttpResponseRedirect(reverse("edit_subject",kwargs={"subject_id":subject_id}))
        except:
            messages.error(request,"Failed to Edit Subject")
            return HttpResponseRedirect(reverse("edit_subject",kwargs={"subject_id":subject_id}))


def edit_department(request,department_id):
    department=Department.objects.get(id=department_id)
    return render(request,"hod_template/edit_department_template.html",{"department":department,"id":department_id})

def edit_department_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        department_id=request.POST.get("department_id")
        department_name=(request.POST.get("department") or "").strip()

        conflict_error = _department_name_conflict(department_name, exclude_department_id=department_id)
        if conflict_error:
            messages.error(request, conflict_error)
            return HttpResponseRedirect(reverse("edit_department",kwargs={"department_id":department_id}))

        try:
            department=Department.objects.get(id=department_id)
            department.department_name=department_name
            department.save()
            messages.success(request,"Successfully Edited Department")
            return HttpResponseRedirect(reverse("edit_department",kwargs={"department_id":department_id}))
        except:
            messages.error(request,"Failed to Edit Department")
            return HttpResponseRedirect(reverse("edit_department",kwargs={"department_id":department_id}))


def manage_semester(request):
    semesters=SemesterModel.object.all()
    return render(request,"hod_template/manage_semester_template.html",{"semesters":semesters})


def delete_semester(request,semester_id):
    try:
        semester=SemesterModel.object.get(id=semester_id)
        semester.delete()
        messages.success(request,"Successfully Deleted Semester")
    except:
        messages.error(request,"Failed to Delete Semester")
    return HttpResponseRedirect(reverse("manage_semester"))


def add_semester_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("manage_semester"))
    else:
        semester_start_date=request.POST.get("semester_start")
        semester_end_date=request.POST.get("semester_end")

        try:
            semester=SemesterModel(semester_start_date=semester_start_date,semester_end_date=semester_end_date)
            semester.save()
            messages.success(request, "Successfully Added Semester")
            return HttpResponseRedirect(reverse("manage_semester"))
        except:
            messages.error(request, "Failed to Add Semester")
            return HttpResponseRedirect(reverse("manage_semester"))

@csrf_exempt
def check_email_exist(request):
    email=_normalize_email(request.POST.get("email"))
    user_obj=CustomUser.objects.filter(email__iexact=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


def staff_feedback_message(request):
    feedbacks=FeedBackStaffs.objects.all()
    return render(request,"hod_template/staff_feedback_template.html",{"feedbacks":feedbacks})

def student_feedback_message(request):
    feedbacks = (
        FeedBackStudent.objects.filter(forwarded_to_hod=True)
        .select_related("student_id__admin", "student_id__semester_id", "staff_id__admin")
        .order_by("-forwarded_at", "-created_at")
    )
    return render(request,"hod_template/student_feedback_template.html",{"feedbacks":feedbacks})

@csrf_exempt
def student_feedback_message_replied(request):
    feedback_id=request.POST.get("id")
    feedback_message=request.POST.get("message")

    try:
        feedback=FeedBackStudent.objects.get(id=feedback_id)
        feedback.hod_reply = feedback_message
        feedback.save(update_fields=["hod_reply"])
        return HttpResponse("True")
    except:
        return HttpResponse("False")

@csrf_exempt
def staff_feedback_message_replied(request):
    feedback_id=request.POST.get("id")
    feedback_message=request.POST.get("message")

    try:
        feedback=FeedBackStaffs.objects.get(id=feedback_id)
        feedback.feedback_reply=feedback_message
        feedback.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")

def staff_leave_view(request):
    leaves=LeaveReportStaff.objects.all()
    return render(request,"hod_template/staff_leave_view.html",{"leaves":leaves})

def student_leave_view(request):
    leaves=LeaveReportStudent.objects.all()
    return render(request,"hod_template/student_leave_view.html",{"leaves":leaves})

def student_approve_leave(request,leave_id):
    leave=LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status=1
    leave.save()
    return HttpResponseRedirect(reverse("student_leave_view"))

def student_disapprove_leave(request,leave_id):
    leave=LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status=2
    leave.save()
    return HttpResponseRedirect(reverse("student_leave_view"))


def staff_approve_leave(request,leave_id):
    leave=LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status=1
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))

def staff_disapprove_leave(request,leave_id):
    leave=LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status=2
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))

def admin_view_attendance(request):
    subjects=Subjects.objects.all()
    semesters=SemesterModel.object.all()
    return render(request,"hod_template/admin_view_attendance.html",{"subjects":subjects,"semesters":semesters})

@csrf_exempt
def admin_get_attendance_dates(request):
    subject=request.POST.get("subject")
    semester_id=request.POST.get("semester_id")
    subject_obj=Subjects.objects.get(id=subject)
    semester_obj=SemesterModel.object.get(id=semester_id)
    attendance=Attendance.objects.filter(subject_id=subject_obj,semester_id=semester_obj)
    attendance_obj=[]
    for attendance_single in attendance:
        data={"id":attendance_single.id,"attendance_date":str(attendance_single.attendance_date),"semester_id":attendance_single.semester_id.id}
        attendance_obj.append(data)

    return JsonResponse(json.dumps(attendance_obj),safe=False)


@csrf_exempt
def admin_get_attendance_student(request):
    attendance_date=request.POST.get("attendance_date")
    attendance=Attendance.objects.get(id=attendance_date)

    attendance_data=AttendanceReport.objects.filter(attendance_id=attendance)
    list_data=[]

    for student in attendance_data:
        data_small={"id":student.student_id.admin.id,"name":student.student_id.admin.first_name+" "+student.student_id.admin.last_name,"status":student.status}
        list_data.append(data_small)
    return JsonResponse(json.dumps(list_data),content_type="application/json",safe=False)

def admin_profile(request):
    user=CustomUser.objects.get(id=request.user.id)
    return render(request,"hod_template/admin_profile.html",{"user":user})

def admin_profile_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("admin_profile"))
    else:
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        notification_email = _normalize_email(request.POST.get("notification_email"))
        password=request.POST.get("password")
        try:
            customuser=CustomUser.objects.get(id=request.user.id)
            customuser.first_name=first_name
            customuser.last_name=last_name
            customuser.notification_email = notification_email or customuser.email
            # if password!=None and password!="":
            #     customuser.set_password(password)
            customuser.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("admin_profile"))
        except:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("admin_profile"))


def reset_imported_student_passwords(request):
    if request.method != "GET":
        return HttpResponseRedirect(reverse("manage_student"))

    reset_count = 0
    for user in CustomUser.objects.filter(
        username__in=IMPORTED_STUDENT_USERNAMES,
        user_type=3,
    ):
        user.set_password("pass12345")
        user.save(update_fields=["password"])
        reset_count += 1

    if reset_count:
        messages.success(
            request,
            f"Reset passwords for {reset_count} imported student account(s). Temporary password: pass12345",
        )
    else:
        messages.warning(request, "No imported student accounts were found to reset.")
    return HttpResponseRedirect(reverse("manage_student"))

def admin_send_notification_student(request):
    students=Students.objects.all()
    return render(request,"hod_template/student_notification.html",{"students":students})

def admin_send_notification_staff(request):
    staffs=Staffs.objects.all()
    return render(request,"hod_template/staff_notification.html",{"staffs":staffs})


def admin_send_notification(request):
    staffs = Staffs.objects.select_related("admin").order_by("admin__first_name", "admin__last_name", "id")
    students = Students.objects.select_related("admin", "class_id__department").order_by("admin__first_name", "admin__last_name", "id")
    departments = Department.objects.order_by("department_name")
    admin_to_staff = {staff.admin_id: staff.id for staff in staffs}
    staff_department_map = {staff.id: [] for staff in staffs}
    for staff_admin_id, department_id in Subjects.objects.values_list("staff_id", "class_id__department_id").distinct():
        staff_id = admin_to_staff.get(staff_admin_id)
        if staff_id:
            staff_department_map[staff_id].append(department_id)
    return render(
        request,
        "hod_template/send_notification.html",
        {
            "staffs": staffs,
            "students": students,
            "departments": departments,
            "staff_department_map_json": json.dumps(staff_department_map),
        },
    )


def send_bulk_notification(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("admin_send_notification"))

    title = (request.POST.get("title") or "").strip()
    message = (request.POST.get("message") or "").strip()
    target_group = (request.POST.get("target_group") or "").strip().lower()
    sender_name = _notification_sender_name(request.user)
    selected_staff_ids = request.POST.getlist("staff_ids")
    selected_student_ids = request.POST.getlist("student_ids")
    selected_department_id = (request.POST.get("department_id") or "").strip()
    selected_staff_department_id = (request.POST.get("staff_department_id") or "").strip()

    if not title:
        messages.error(request, "Notification title is required")
        return HttpResponseRedirect(reverse("admin_send_notification"))

    if not message:
        messages.error(request, "Notification body is required")
        return HttpResponseRedirect(reverse("admin_send_notification"))

    if target_group not in {"staff", "student", "all"}:
        messages.error(request, "Please select whom to send")
        return HttpResponseRedirect(reverse("admin_send_notification"))

    staff_qs = Staffs.objects.none()
    student_qs = Students.objects.none()

    if target_group == "all":
        staff_qs = Staffs.objects.all()
        student_qs = Students.objects.all()
    elif target_group == "staff":
        filtered_staff_qs = Staffs.objects.all()
        if selected_staff_department_id and selected_staff_department_id != "all_departments":
            filtered_staff_qs = filtered_staff_qs.filter(
                admin_id__in=Subjects.objects.filter(class_id__department_id=selected_staff_department_id)
                .values_list("staff_id", flat=True)
                .distinct()
            )
        if not selected_staff_ids:
            messages.error(request, "Please select at least one staff member")
            return HttpResponseRedirect(reverse("admin_send_notification"))
        staff_qs = filtered_staff_qs.filter(id__in=selected_staff_ids)
    else:
        if not selected_department_id:
            messages.error(request, "Please select a department for students")
            return HttpResponseRedirect(reverse("admin_send_notification"))
        department_students = Students.objects.all()
        if selected_department_id != "all_departments":
            department_students = department_students.filter(class_id__department_id=selected_department_id)
        if not selected_student_ids:
            messages.error(request, "Please select at least one student")
            return HttpResponseRedirect(reverse("admin_send_notification"))
        student_qs = department_students.filter(id__in=selected_student_ids)

    staff_recipients = list(staff_qs)
    student_recipients = list(student_qs)

    if not staff_recipients and not student_recipients:
        messages.error(request, "No recipients found for selected options")
        return HttpResponseRedirect(reverse("admin_send_notification"))

    if staff_recipients:
        NotificationStaffs.objects.bulk_create(
            [
                NotificationStaffs(
                    staff_id=staff,
                    sender_name=sender_name,
                    title=title,
                    message=message,
                )
                for staff in staff_recipients
            ]
        )
    if student_recipients:
        create_student_notifications(
            student_recipients,
            sender_name=sender_name,
            title=title,
            message=message,
        )
        send_student_notification_emails(
            student_recipients,
            sender_name=sender_name,
            title=title,
            message=message,
        )

    messages.success(
        request,
        f"Notification sent to {len(staff_recipients)} staff and {len(student_recipients)} students.",
    )
    return HttpResponseRedirect(reverse("admin_send_notification"))

@csrf_exempt
def send_student_notification(request):
    id=request.POST.get("id")
    title = (request.POST.get("title") or "Student Management System").strip()
    message=request.POST.get("message")
    sender_name = _notification_sender_name(request.user)
    student=Students.objects.get(admin=id)
    token=student.fcm_token
    url="https://fcm.googleapis.com/fcm/send"
    body={
        "notification":{
            "title": title,
            "body":message,
            "click_action": "https://studentmanagementsystem22.herokuapp.com/student_all_notification",
            "icon": "http://studentmanagementsystem22.herokuapp.com/static/dist/img/user2-160x160.jpg"
        },
        "to":token
    }
    headers={"Content-Type":"application/json","Authorization":"key=SERVER_KEY_HERE"}
    data=requests.post(url,data=json.dumps(body),headers=headers)
    notification=NotificationStudent(student_id=student,sender_name=sender_name,title=title,message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")

@csrf_exempt
def send_staff_notification(request):
    id=request.POST.get("id")
    title = (request.POST.get("title") or "Student Management System").strip()
    message=request.POST.get("message")
    sender_name = _notification_sender_name(request.user)
    staff=Staffs.objects.get(admin=id)
    token=staff.fcm_token
    url="https://fcm.googleapis.com/fcm/send"
    body={
        "notification":{
            "title": title,
            "body":message,
            "click_action":"https://studentmanagementsystem22.herokuapp.com/staff_all_notification",
            "icon":"http://studentmanagementsystem22.herokuapp.com/static/dist/img/user2-160x160.jpg"
        },
        "to":token
    }
    headers={"Content-Type":"application/json","Authorization":"key=SERVER_KEY_HERE"}
    data=requests.post(url,data=json.dumps(body),headers=headers)
    notification=NotificationStaffs(staff_id=staff,sender_name=sender_name,title=title,message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")
