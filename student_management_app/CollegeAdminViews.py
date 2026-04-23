from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
import csv
import openpyxl
from io import TextIOWrapper
from django.db import transaction
from student_management_app.models import CustomUser, Institution, Staffs, Students, Department, Subjects, StudentResult

def collegeadmin_home(request):
    institution = request.user.institution
    if not institution:
        messages.error(request, "No institution assigned")
        return HttpResponseRedirect(reverse("show_login"))

    student_count = Students.objects.filter(admin__institution=institution).count()
    staff_count = Staffs.objects.filter(admin__institution=institution).count()

    context = {
        "student_count": student_count,
        "staff_count": staff_count,
    }
    return render(request, "collegeadmin_template/home_content.html", context)

def collegeadmin_manage_grades(request):
    return render(request, "collegeadmin_template/manage_grades.html")

def collegeadmin_manage_grades_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("collegeadmin_manage_grades"))
    try:
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "No file uploaded.")
            return HttpResponseRedirect(reverse("collegeadmin_manage_grades"))

        if file.name.endswith('.csv'):
            csv_file = TextIOWrapper(file.file, encoding='utf-8')
            reader = csv.DictReader(csv_file)
            data = list(reader)
        elif file.name.endswith(('.xls', '.xlsx')):
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            data = []
            headers = [cell.value for cell in sheet[1]]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                data.append(dict(zip(headers, row)))
        else:
            messages.error(request, "Unsupported file format. Please upload CSV or Excel.")
            return HttpResponseRedirect(reverse("collegeadmin_manage_grades"))

        required_cols = {"student_profile_id", "subject_name", "exam_marks", "assignment_marks"}
        if not data:
            messages.error(request, "File is empty.")
            return HttpResponseRedirect(reverse("collegeadmin_manage_grades"))
        
        if not required_cols.issubset(set(data[0].keys())):
            messages.error(request, f"Missing required columns. Expected: {', '.join(required_cols)}")
            return HttpResponseRedirect(reverse("collegeadmin_manage_grades"))

        success_count = 0
        error_count = 0
        institution = request.user.institution

        with transaction.atomic():
            for row in data:
                try:
                    student_profile_id = str(row["student_profile_id"]).strip()
                    subject_name = str(row["subject_name"]).strip()
                    exam_marks = float(row["exam_marks"])
                    assignment_marks = float(row["assignment_marks"])

                    student = Students.objects.get(profile_id=student_profile_id, admin__institution=institution)
                    subject = Subjects.objects.get(subject_name__iexact=subject_name, class_id__department__institution=institution)

                    result, created = StudentResult.objects.get_or_create(
                        student_id=student,
                        subject_id=subject,
                        defaults={
                            "subject_exam_marks": exam_marks,
                            "subject_assignment_marks": assignment_marks,
                            "grade_letter": ""
                        }
                    )
                    if not created:
                        result.subject_exam_marks = exam_marks
                        result.subject_assignment_marks = assignment_marks
                        result.save()
                    success_count += 1
                except (Students.DoesNotExist, Subjects.DoesNotExist, ValueError, KeyError):
                    error_count += 1
                    continue

        messages.success(request, f"Grades uploaded: {success_count} successful, {error_count} failed.")
        return HttpResponseRedirect(reverse("collegeadmin_manage_grades"))
    except Exception as e:
        messages.error(request, f"Failed to upload grades: {str(e)}")
        return HttpResponseRedirect(reverse("collegeadmin_manage_grades"))
def collegeadmin_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    return render(request, "collegeadmin_template/collegeadmin_profile.html", {"user": user})

def collegeadmin_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("collegeadmin_profile"))
    
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    password = request.POST.get("password")

    try:
        user = CustomUser.objects.get(id=request.user.id)
        user.first_name = first_name
        user.last_name = last_name
        if password and password.strip():
            user.set_password(password)
        user.save()
        messages.success(request, "Profile Updated Successfully")
    except Exception as e:
        messages.error(request, f"Failed to Update Profile: {str(e)}")
    return HttpResponseRedirect(reverse("collegeadmin_profile"))
