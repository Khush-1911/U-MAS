from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from student_management_app.models import CustomUser, Institution, Staffs, Students, Department, HOD, Timetable

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

    student_count = Students.objects.filter(department_id=department).count()
    staff_count = Staffs.objects.filter(admin__institution=department.institution).count() # This should actually be filtered by department, but staffs don't have a direct department relation in U-MAS by default without subjects.

    context = {
        "student_count": student_count,
        "staff_count": staff_count,
        "department_name": department.department_name
    }
    return render(request, "department_hod_template/home_content.html", context)

def department_hod_upload_timetable(request):
    return render(request, "department_hod_template/upload_timetable.html")

def department_hod_upload_timetable_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("department_hod_upload_timetable"))
    
    try:
        hod_profile = HOD.objects.get(admin=request.user)
        department = hod_profile.department
        timetable_file = request.FILES.get("timetable_file")

        if timetable_file:
            # Save or update timetable
            timetable, created = Timetable.objects.get_or_create(department=department)
            timetable.timetable_file = timetable_file
            timetable.save()
            messages.success(request, "Timetable Successfully Uploaded")
        else:
            messages.error(request, "Please provide a valid file.")
    except Exception as e:
        messages.error(request, f"Failed to upload timetable: {str(e)}")
        
    return HttpResponseRedirect(reverse("department_hod_upload_timetable"))
