from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from student_management_app.models import Students, Staffs, Subjects, Department

def superuser_home(request):
    institution = request.user.institution
    if not institution:
        messages.error(request, "No institution assigned")
        return HttpResponseRedirect(reverse("show_login"))

    student_count = Students.objects.filter(admin__institution=institution).count()
    staff_count = Staffs.objects.filter(admin__institution=institution).count()
    subject_count = Subjects.objects.filter(class_id__department__institution=institution).count()
    department_count = Department.objects.filter(institution=institution).count()

    context = {
        "student_count": student_count,
        "staff_count": staff_count,
        "subject_count": subject_count,
        "department_count": department_count,
    }
    return render(request, "hod_template/home_content.html", context)
