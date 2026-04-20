from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from student_management_app.models import CustomUser, Institution, Staffs, Students, Department, HOD, Timetable, ClassModel, SemesterModel

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
    staff_count = Staffs.objects.filter(admin__institution=department.institution).count() # This should actually be filtered by department, but staffs don't have a direct department relation in U-MAS by default without subjects.

    context = {
        "student_count": student_count,
        "staff_count": staff_count,
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
    semesters = SemesterModel.object.all()
    
    return render(request, "department_hod_template/upload_timetable.html", {"classes": classes, "semesters": semesters})

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
            semester_obj = SemesterModel.object.get(id=semester_id)
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
