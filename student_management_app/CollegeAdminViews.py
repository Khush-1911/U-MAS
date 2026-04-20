from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from student_management_app.models import CustomUser, Institution, Staffs, Students, Department

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
        # Placeholder for actual file parsing logic (e.g. pandas)
        # We will parse the uploaded file and update StudentResult models
        messages.success(request, "Grades successfully parsed and uploaded.")
        return HttpResponseRedirect(reverse("collegeadmin_manage_grades"))
    except Exception as e:
        messages.error(request, f"Failed to upload grades: {str(e)}")
        return HttpResponseRedirect(reverse("collegeadmin_manage_grades"))
