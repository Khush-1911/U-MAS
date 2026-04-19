import datetime
import json
import os

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from student_management_app.EmailBackEnd import EmailBackEnd
from student_management_app.models import CustomUser, Courses, SemesterModel, OnlineClassRoom, Staffs, Students
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
    return render(
        request,
        "login_page.html",
        {
            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
            "recaptcha_login_action": settings.RECAPTCHA_LOGIN_ACTION,
        },
    )

def doLogin(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        captcha_token = (request.POST.get("g-recaptcha-response") or "").strip()
        captcha_secret = os.getenv("RECAPTCHA_SECRET_KEY", "").strip()
        captcha_enabled = bool(settings.RECAPTCHA_SITE_KEY and captcha_secret)
        should_verify_captcha = captcha_enabled and (bool(captcha_token) or not settings.DEBUG)

        if not settings.DEBUG and not captcha_enabled:
            messages.error(request, "Captcha is not configured on the server.")
            return HttpResponseRedirect("/")

        if captcha_enabled and not captcha_token:
            messages.error(request, "Captcha verification did not complete. Please try again.")
            return HttpResponseRedirect("/")

        if should_verify_captcha:
            cap_url = "https://www.google.com/recaptcha/api/siteverify"
            cap_data = {"secret": captcha_secret, "response": captcha_token}
            try:
                cap_server_response = requests.post(url=cap_url, data=cap_data, timeout=10)
                cap_json = cap_server_response.json()
            except (requests.RequestException, json.JSONDecodeError, ValueError):
                if settings.DEBUG:
                    messages.warning(request, "Captcha verification unavailable in debug mode. Continuing login.")
                    cap_json = {"success": True}
                else:
                    messages.error(request, "Captcha verification failed. Please try again.")
                    return HttpResponseRedirect("/")

            if not cap_json.get("success", False):
                messages.error(request,"Invalid Captcha. Try again.")
                return HttpResponseRedirect("/")

            if cap_json.get("action") and cap_json.get("action") != settings.RECAPTCHA_LOGIN_ACTION:
                messages.error(request, "Captcha action mismatch. Please refresh and try again.")
                return HttpResponseRedirect("/")

            score = cap_json.get("score")
            if score is not None and score < settings.RECAPTCHA_MIN_SCORE:
                messages.error(request, "Captcha score too low. Please try again.")
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
    if request.user.is_authenticated:
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
        if student.course_id.id != room.subject.course_id.id or student.semester_id.id != room.semester.id:
            return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
        if student.assigned_staff_id and student.assigned_staff_id != room.started_by_id:
            return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    else:
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)

    return JsonResponse({"ok": True, "room": serialize_room_state(room)})

