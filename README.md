# U-MAS (University Management & Attendance System)

U-MAS is a Django-based multi-role web application for managing university operations: students, staff, courses, subjects, sessions, attendance, leave, feedback, notifications, results, and live classrooms.

## 1. Tech Stack

### Backend
- Python 3.x
- Django (project currently runs on modern Django in this environment)
- Django custom user model (`student_management_app.CustomUser`)
- SQLite (default)
- Optional MySQL-style configuration support via environment variables

### Frontend
- Django Templates (server-rendered pages)
- Custom CSS theme (`student_management_app/static/ui/app.css`)
- Bootstrap assets (local static files)
- Font Awesome icons
- jQuery
- Chart.js (dashboard charts)

### Real-time / Integrations
- Google reCAPTCHA validation on login
- Firebase messaging service worker endpoint (template/stub config)
- RTCMultiConnection-based live classroom pages

## 2. Project Structure

- `manage.py`: Django management entry point
- `student_management_system/`: project settings and URL routing
- `student_management_app/`: app logic (models, views, templates, static)
- `student_management_app/models.py`: core data model
- `student_management_app/HodViews.py`: HOD/Admin feature views
- `student_management_app/StaffViews.py`: Staff feature views
- `student_management_app/StudentViews.py`: Student feature views
- `student_management_app/templates/`: UI templates
- `student_management_app/static/`: CSS/JS/images/plugins
- `.env.example`: safe environment variable template
- `.gitignore`: excludes secrets, DB files, venvs, generated files

## 3. Data Model Overview

Main entities:
- `CustomUser` with role type: HOD (`1`), Staff (`2`), Student (`3`)
- `AdminHOD`, `Staffs`, `Students` (role profiles)
- `Courses`, `Subjects`, `SessionYearModel`
- `Attendance`, `AttendanceReport`
- `LeaveReportStaff`, `LeaveReportStudent`
- `FeedBackStaffs`, `FeedBackStudent`
- `NotificationStaffs`, `NotificationStudent`
- `StudentResult`
- `OnlineClassRoom`

## 4. Environment Configuration

This project reads sensitive/runtime values from environment variables in `student_management_system/settings.py`.

Use `.env.example` as reference:

```env
DJANGO_SECRET_KEY=replace-with-secure-secret
DJANGO_DEBUG=True
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

Notes:
- SQLite is default if DB variables are not overridden.
- Do not commit `.env` or actual credentials.

## 5. How to Run Locally

### Step 1: Create and activate virtual environment

```bash
cd "/Users/buntie/Desktop/Project ETC/U-MAS"
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install dependencies

No `requirements.txt` is currently committed. Install minimum required packages:

```bash
pip install django requests
```

If you use MySQL, also install an appropriate DB driver (example):

```bash
pip install mysqlclient
```

### Step 3: Export environment variables (or use your shell profile)

```bash
export DJANGO_SECRET_KEY="change-this"
export DJANGO_DEBUG="True"
```

### Step 4: Apply migrations

```bash
python3 manage.py migrate
```

### Step 5: Run server

```bash
python3 manage.py runserver
```

Open:
- App: `http://127.0.0.1:8000/`
- Django admin: `http://127.0.0.1:8000/admin/`

## 6. Initial Setup Requirements (Important)

Some code paths assume base records exist.

1. Ensure at least one Course exists with ID `1`.
2. Ensure at least one Session exists with ID `1`.

Reason: `post_save` signal for student profile creation references `Courses.objects.get(id=1)` and `SessionYearModel.object.get(id=1)`.

Recommended order for first-time setup:
1. Create HOD/Admin account (`/signup_admin`)
2. Login as HOD
3. Add course(s)
4. Add session year(s)
5. Add staff
6. Add subject(s)
7. Add student(s)

## 7. Role-Based Features and How to Use Them

## HOD / Admin

Entry page after login: `/admin_home`

### Dashboard
- View totals: Students, Staff, Courses, Subjects
- View analytics charts for attendance and distribution

### Staff Management
- Add staff: `/add_staff`
- Manage staff: `/manage_staff`
- Edit staff: `/edit_staff/<staff_id>`
- Delete staff: `/delete_staff/<staff_id>`

### Student Management
- Add student: `/add_student`
- Manage students: `/manage_student`
- Edit student: `/edit_student/<student_id>`
- Delete student: `/delete_student/<student_id>`

### Course Management
- Add course: `/add_course/`
- Manage courses: `/manage_course`
- Edit course: `/edit_course/<course_id>`
- Delete course: `/delete_course/<course_id>`

### Subject Management
- Add subject: `/add_subject`
- Manage subjects: `/manage_subject`
- Edit subject: `/edit_subject/<subject_id>`
- Delete subject: `/delete_subject/<subject_id>`

### Session Management
- Manage/add sessions: `/manage_session`
- Delete session: `/delete_session/<session_id>`

### Leave Management
- Student leave requests: `/student_leave_view`
- Staff leave requests: `/staff_leave_view`
- Approve/disapprove actions available from listing pages

### Attendance Oversight
- View attendance by subject/session/date: `/admin_view_attendance`

### Feedback and Notifications
- Student/staff feedback review + reply endpoints exist
- Send notifications to staff/students via Firebase endpoints

### Profile
- Update HOD profile: `/admin_profile`

## Staff

Entry page after login: `/staff_home`

### Dashboard
- View students under taught courses
- Attendance counts and subject-wise analytics

### Attendance
- Take attendance: `/staff_take_attendance`
- Update attendance: `/staff_update_attendance`
- Save endpoints: `save_attendance_data`, `save_updateattendance_data`

### Leave
- Apply leave: `/staff_apply_leave`

### Feedback
- Submit feedback: `/staff_feedback`

### Profile
- Update profile/password/address: `/staff_profile`

### Notifications
- Save FCM token: `/staff_fcmtoken_save`
- View notifications: `/staff_all_notification`

### Student Results
- Add/update marks: `/staff_add_result`
- Edit results via class-based view route: `/edit_student_result`

### Live Classroom
- Start classroom: `/start_live_classroom`
- Process room creation/join data: `/start_live_classroom_process`

## Student

Entry page after login: `/student_home`

### Dashboard
- Total/present/absent attendance summary
- Subject attendance chart
- Active live classroom list for current session

### Live Classroom
- Join classroom: `/join_class_room/<subject_id>/<session_year_id>`

### Attendance
- Attendance filter by subject/date range: `/student_view_attendance`

### Leave
- Apply leave: `/student_apply_leave`

### Feedback
- Submit feedback: `/student_feedback`

### Profile
- Update profile/password/address: `/student_profile`

### Notifications
- Save FCM token: `/student_fcmtoken_save`
- View notifications: `/student_all_notification`

### Results
- View subject result records: `/student_view_result`

## 8. Authentication and Authorization

- Login route: `/`
- Login processor: `/doLogin`
- Logout: `/logout_user`
- Role-based redirects after login:
  - HOD -> `/admin_home`
  - Staff -> `/staff_home`
  - Student -> `/student_home`
- Middleware enforces role-based path access (`LoginCheckMiddleWare`)

## 9. Security and Production Notes

Current codebase is suitable for development and learning deployments. Before production:

1. Set `DJANGO_DEBUG=False`
2. Set strict `ALLOWED_HOSTS`
3. Use a strong secret key from environment
4. Move reCAPTCHA secret key out of source code
5. Replace placeholder Firebase server keys
6. Use production DB credentials via environment variables
7. Serve static/media with proper production setup (Nginx + Gunicorn/Uvicorn)
8. Enable HTTPS and secure cookie settings

## 10. Common Commands

```bash
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

## 11. Recent Project Changes Included

- Custom modern UI theme replaces AdminLTE dependency usage in templates
- HOD management pages support delete actions for:
  - Staff
  - Students
  - Subjects
  - Courses
  - Sessions
- Staff/Student manage lists now display role-table IDs for clearer separation
- Last login column removed from HOD staff/student manage pages
- Settings updated for environment-based secret and DB config

---

If you want, the next improvement is adding a `requirements.txt` and `docker-compose.yml` so setup is one command and fully reproducible.
