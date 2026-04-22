from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from student_management_app.models import CustomUser, Institution, Staffs, Students, Department

def owner_home(request):
    institutions = Institution.objects.all()
    institution_count = institutions.count()
    student_count = Students.objects.all().count()
    staff_count = Staffs.objects.all().count()
    department_count = Department.objects.all().count()

    institution_name_list = []
    student_count_list = []
    staff_count_list = []

    for inst in institutions:
        institution_name_list.append(inst.name)
        student_count_list.append(Students.objects.filter(admin__institution=inst).count())
        staff_count_list.append(Staffs.objects.filter(admin__institution=inst).count())

    context = {
        "institution_count": institution_count,
        "student_count": student_count,
        "staff_count": staff_count,
        "department_count": department_count,
        "institution_name_list": institution_name_list,
        "student_count_list": student_count_list,
        "staff_count_list": staff_count_list,
        "institutions": institutions
    }
    return render(request, "owner_template/home_content.html", context)

def add_institution(request):
    return render(request, "owner_template/add_institution.html")

def add_institution_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("add_institution"))
    else:
        name = request.POST.get("name")
        address = request.POST.get("address")
        contact_email = request.POST.get("contact_email")
        try:
            Institution.objects.create(name=name, address=address, contact_email=contact_email)
            messages.success(request, "Institution Created Successfully")
        except Exception:
            messages.error(request, "Failed to create institution")
        return HttpResponseRedirect(reverse("add_institution"))

def add_user(request):
    institutions = Institution.objects.all()
    roles = [
        {"id": "2", "name": "Staff"},
        {"id": "3", "name": "Student"},
        {"id": "4", "name": "Superuser"},
        {"id": "5", "name": "Principal"},
        {"id": "6", "name": "College Admin"},
        {"id": "7", "name": "HOD"},
    ]
    return render(request, "owner_template/add_user.html", {"institutions": institutions, "roles": roles})

from django.db import transaction

def add_user_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("add_user"))
    
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    email = request.POST.get("email")
    password = request.POST.get("password")
    role_id = request.POST.get("role")
    institution_id = request.POST.get("institution")

    try:
        institution = Institution.objects.get(id=institution_id)
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                username=email, # Use email as username
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                user_type=role_id,
            )
            user.institution = institution
            user.save()
        messages.success(request, "Successfully Added User to Institution")
        return HttpResponseRedirect(reverse("add_user"))
    except Exception as e:
        messages.error(request, f"Failed to add user: {str(e)}")
        return HttpResponseRedirect(reverse("add_user"))

def manage_institutions(request):
    institutions = Institution.objects.all()
    return render(request, "owner_template/manage_institutions.html", {"institutions": institutions})

def delete_institution(request, institution_id):
    try:
        institution = Institution.objects.get(id=institution_id)
        institution.delete()
        messages.success(request, "Institution Deleted Successfully")
    except Exception:
        messages.error(request, "Failed to delete institution")
    return HttpResponseRedirect(reverse("manage_institutions"))

def manage_users(request):
    users = CustomUser.objects.all().exclude(id=request.user.id)
    return render(request, "owner_template/manage_users.html", {"users": users})

def delete_user(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        user.delete()
        messages.success(request, "User Deleted Successfully")
    except Exception:
        messages.error(request, "Failed to delete user")
    return HttpResponseRedirect(reverse("manage_users"))
