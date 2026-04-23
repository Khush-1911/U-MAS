from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from student_management_app.models import CustomUser, Institution, Staffs, Students, Department, Principal, CollegeAdmin, HOD

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

def principal_edit_user(request, user_id):
    institution = request.user.institution
    user_obj = CustomUser.objects.get(id=user_id, institution=institution)
    institutions = Institution.objects.all() # Or restrict to their own? User said "move users from an institution"
    roles = [
        {"id": "2", "name": "Staff"},
        {"id": "3", "name": "Student"},
        {"id": "6", "name": "College Admin"},
        {"id": "7", "name": "HOD"},
    ]
    return render(request, "principal_template/edit_user.html", {"user_obj": user_obj, "institutions": institutions, "roles": roles})

from django.db import transaction

def principal_edit_user_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("principal_manage_users"))
    
    institution_auth = request.user.institution
    user_id = request.POST.get("user_id")
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    email = request.POST.get("email")
    role_id = request.POST.get("role")
    institution_id = request.POST.get("institution")

    try:
        user = CustomUser.objects.get(id=user_id, institution=institution_auth)
        institution = Institution.objects.get(id=institution_id)
        
        with transaction.atomic():
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = email
            user.user_type = role_id
            user.institution = institution
            user.save()

            # Profile creation logic
            if role_id == "2" and not hasattr(user, 'staffs'):
                Staffs.objects.create(admin=user, address="")
            elif role_id == "3" and not hasattr(user, 'students'):
                Students.objects.create(admin=user, address="", gender="", mentor=None)
            elif role_id == "6" and not hasattr(user, 'collegeadmin'):
                CollegeAdmin.objects.create(admin=user)
            elif role_id == "7" and not hasattr(user, 'hod'):
                HOD.objects.create(admin=user)
            
        messages.success(request, "User Updated Successfully")
        return HttpResponseRedirect(reverse("principal_edit_user", kwargs={"user_id": user_id}))
    except Exception as e:
        messages.error(request, f"Failed to update user: {str(e)}")
        return HttpResponseRedirect(reverse("principal_manage_users"))
def principal_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    return render(request, "principal_template/principal_profile.html", {"user": user})

def principal_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("principal_profile"))
    
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
    return HttpResponseRedirect(reverse("principal_profile"))
