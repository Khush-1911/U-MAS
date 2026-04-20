from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from student_management_app.models import CustomUser, Institution, Staffs, Students, Department

def principal_home(request):
    institution = request.user.institution
    if not institution:
        messages.error(request, "No institution assigned")
        return HttpResponseRedirect(reverse("show_login"))

    student_count = Students.objects.filter(admin__institution=institution).count()
    staff_count = Staffs.objects.filter(admin__institution=institution).count()
    department_count = Department.objects.filter(institution=institution).count()

    context = {
        "student_count": student_count,
        "staff_count": staff_count,
        "department_count": department_count,
    }
    return render(request, "principal_template/home_content.html", context)

def principal_manage_users(request):
    institution = request.user.institution
    users = CustomUser.objects.filter(institution=institution).exclude(id=request.user.id)
    return render(request, "principal_template/manage_users.html", {"users": users})
