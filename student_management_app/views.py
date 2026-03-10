import datetime
import json
import os

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from student_management_app.EmailBackEnd import EmailBackEnd
from student_management_app.models import CustomUser, Courses, SessionYearModel, OnlineClassRoom, Staffs, Students
from student_management_app.services.live_class_service import serialize_room_state
from student_management_system import settings


def _normalize_email(value):
    return (value or "").strip().lower()


def _credentials_error(username, email, exclude_user_id=None):
    username = (username or "").strip()
    email = _normalize_email(email)

    if not username or not email:
        return "Username and email are required"

    username_qs = CustomUser.objects.filter(username__iexact=username)
    email_qs = CustomUser.objects.filter(email__iexact=email)
    if exclude_user_id:
        username_qs = username_qs.exclude(id=exclude_user_id)
        email_qs = email_qs.exclude(id=exclude_user_id)

    if username_qs.exists():
        return "Username already exists"
    if email_qs.exists():
        return "Email already exists"
    return None


def ShowLoginPage(request):
    return render(request,"login_page.html")

def doLogin(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        captcha_token=request.POST.get("g-recaptcha-response")
        cap_url="https://www.google.com/recaptcha/api/siteverify"
        cap_secret=os.getenv("RECAPTCHA_SECRET_KEY", "6LeWtqUZAAAAANlv3se4uw5WAg-p0X61CJjHPxKT")
        cap_data={"secret":cap_secret,"response":captcha_token}
        cap_server_response=requests.post(url=cap_url,data=cap_data,timeout=10)
        cap_json=json.loads(cap_server_response.text)

        if cap_json['success']==False:
            messages.error(request,"Invalid Captcha Try Again")
            return HttpResponseRedirect("/")

        user=EmailBackEnd.authenticate(request,username=request.POST.get("email"),password=request.POST.get("password"))
        if user!=None:
            login(request,user)
            if user.user_type=="1":
                return HttpResponseRedirect('/admin_home')
            elif user.user_type=="2":
                return HttpResponseRedirect(reverse("staff_home"))
            else:
                return HttpResponseRedirect(reverse("student_home"))
        else:
            messages.error(request,"Invalid Login Details")
            return HttpResponseRedirect("/")


def GetUserDetails(request):
    if request.user!=None:
        return HttpResponse("User : "+request.user.email+" usertype : "+str(request.user.user_type))
    else:
        return HttpResponse("Please Login First")

def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")

def showFirebaseJS(request):
    data='importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-app.js");' \
         'importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-messaging.js"); ' \
         'var firebaseConfig = {' \
         '        apiKey: "YOUR_API_KEY",' \
         '        authDomain: "FIREBASE_AUTH_URL",' \
         '        databaseURL: "FIREBASE_DATABASE_URL",' \
         '        projectId: "FIREBASE_PROJECT_ID",' \
         '        storageBucket: "FIREBASE_STORAGE_BUCKET_URL",' \
         '        messagingSenderId: "FIREBASE_SENDER_ID",' \
         '        appId: "FIREBASE_APP_ID",' \
         '        measurementId: "FIREBASE_MEASUREMENT_ID"' \
         ' };' \
         'firebase.initializeApp(firebaseConfig);' \
         'const messaging=firebase.messaging();' \
         'messaging.setBackgroundMessageHandler(function (payload) {' \
         '    console.log(payload);' \
         '    const notification=JSON.parse(payload);' \
         '    const notificationOption={' \
         '        body:notification.body,' \
         '        icon:notification.icon' \
         '    };' \
         '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
         '});'

    return HttpResponse(data,content_type="text/javascript")

def Testurl(request):
    return HttpResponse("Ok")


def live_class_room_state_api(request, room_id):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "Login required"}, status=403)

    try:
        room = OnlineClassRoom.objects.get(id=room_id)
    except ObjectDoesNotExist:
        return JsonResponse({"ok": False, "error": "Room not found"}, status=404)

    user_type = str(request.user.user_type)
    if user_type == "2":
        if room.started_by.admin_id != request.user.id:
            return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    elif user_type == "3":
        student = Students.objects.get(admin=request.user.id)
        if student.course_id.id != room.subject.course_id.id or student.session_year_id.id != room.session_years.id:
            return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
        if student.assigned_staff_id and student.assigned_staff_id != room.started_by_id:
            return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    else:
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)

    return JsonResponse({"ok": True, "room": serialize_room_state(room)})

def signup_admin(request):
    return render(request,"signup_admin_page.html")

def signup_student(request):
    courses=Courses.objects.all()
    session_years=SessionYearModel.object.all()
    staffs=Staffs.objects.select_related("admin").all()
    if not staffs.exists():
        messages.error(request, "No staff accounts found. Student signup is temporarily unavailable.")
    return render(
        request,
        "signup_student_page.html",
        {"courses":courses,"session_years":session_years,"staffs":staffs},
    )

def signup_staff(request):
    return render(request,"signup_staff_page.html")

def do_admin_signup(request):
    username=request.POST.get("username", "").strip()
    email=_normalize_email(request.POST.get("email"))
    password=request.POST.get("password")

    error = _credentials_error(username, email)
    if error:
        messages.error(request, error)
        return HttpResponseRedirect(reverse("show_login"))
    if not password:
        messages.error(request, "Password is required")
        return HttpResponseRedirect(reverse("show_login"))

    try:
        with transaction.atomic():
            user=CustomUser.objects.create_user(username=username,password=password,email=email,user_type=1)
            user.save()
        messages.success(request,"Successfully Created Admin")
        return HttpResponseRedirect(reverse("show_login"))
    except IntegrityError:
        messages.error(request,"Email already exists")
        return HttpResponseRedirect(reverse("show_login"))
    except Exception:
        messages.error(request,"Failed to Create Admin")
        return HttpResponseRedirect(reverse("show_login"))

def do_staff_signup(request):
    username=request.POST.get("username", "").strip()
    email=_normalize_email(request.POST.get("email"))
    password=request.POST.get("password")
    address=request.POST.get("address", "").strip()

    if not username or not email or not password:
        messages.error(request, "Username, email, and password are required")
        return HttpResponseRedirect(reverse("show_login"))

    error = _credentials_error(username, email)
    if error:
        messages.error(request, error)
        return HttpResponseRedirect(reverse("show_login"))

    try:
        with transaction.atomic():
            user=CustomUser.objects.create_user(username=username,password=password,email=email,user_type=2)
            user.staffs.address=address
            user.staffs.save(update_fields=["address"])
        messages.success(request,"Successfully Created Staff")
        return HttpResponseRedirect(reverse("show_login"))
    except IntegrityError:
        messages.error(request,"Email already exists")
        return HttpResponseRedirect(reverse("show_login"))
    except Exception:
        messages.error(request,"Failed to Create Staff")
        return HttpResponseRedirect(reverse("show_login"))

def do_signup_student(request):
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    username = request.POST.get("username", "").strip()
    email = _normalize_email(request.POST.get("email"))
    password = request.POST.get("password")
    address = request.POST.get("address", "").strip()
    session_year_id = request.POST.get("session_year")
    course_id = request.POST.get("course")
    sex = request.POST.get("sex", "").strip()
    assigned_staff_id = request.POST.get("assigned_staff")

    if not all([first_name, last_name, username, email, password, address, session_year_id, course_id, sex, assigned_staff_id]):
        messages.error(request, "All fields are required")
        return HttpResponseRedirect(reverse("show_login"))

    error = _credentials_error(username, email)
    if error:
        messages.error(request, error)
        return HttpResponseRedirect(reverse("show_login"))

    profile_pic = request.FILES.get("profile_pic")
    if not profile_pic:
        messages.error(request, "Profile picture is required")
        return HttpResponseRedirect(reverse("show_login"))

    fs = FileSystemStorage()
    filename = fs.save(profile_pic.name, profile_pic)
    profile_pic_url = fs.url(filename)

    try:
        with transaction.atomic():
            course_obj = Courses.objects.get(id=course_id)
            session_year = SessionYearModel.object.get(id=session_year_id)
            assigned_staff = Staffs.objects.select_related("admin").get(id=assigned_staff_id)

            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email,
                last_name=last_name,
                first_name=first_name,
                user_type=3,
            )
            user.students.address = address
            user.students.course_id = course_obj
            user.students.session_year_id = session_year
            user.students.gender = sex
            user.students.profile_pic = profile_pic_url
            user.students.assigned_staff = assigned_staff
            user.students.save()

        messages.success(request, "Successfully Added Student")
        return HttpResponseRedirect(reverse("show_login"))
    except (Courses.DoesNotExist, SessionYearModel.DoesNotExist, Staffs.DoesNotExist):
        messages.error(request, "Invalid course, session year, or assigned staff")
        return HttpResponseRedirect(reverse("show_login"))
    except IntegrityError:
        messages.error(request, "Email already exists")
        return HttpResponseRedirect(reverse("show_login"))
    except Exception:
       messages.error(request, "Failed to Add Student")
       return HttpResponseRedirect(reverse("show_login"))
