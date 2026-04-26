# U-MAS (University Management & Attendance System)

[![Django](https://img.shields.io/badge/Django-4.2+-092e20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169e1?style=for-the-badge&logo=postgresql)](https://neon.tech/)
[![Render](https://img.shields.io/badge/Render-Deployed-46E3B7?style=for-the-badge&logo=render)](https://render.com/)

U-MAS is a comprehensive, production-ready Django-based Student Management System (SMS) designed to streamline university operations. It features a modern, role-based architecture with a premium user interface powered by the **Editorial Ether** design system.

---

## ✨ Key Features

- **🎨 Modern UI/UX**: Built with the "Editorial Ether" design system, featuring glassmorphism, fluid animations, and a high-contrast palette.
- **🔐 Multi-Role Architecture**: Specialized dashboards for Owner, Principal, Superuser (HOD), College Admin, Staff, and Students.
- **📊 Real-time Analytics**: Interactive charts (Chart.js) for attendance, performance tracking, and resource distribution.
- **🎥 Live Classrooms**: Integrated real-time virtual classroom support via RTCMultiConnection.
- **📝 Attendance Management**: Streamlined attendance tracking for staff with comprehensive reports for students and HODs.
- **📄 Result Management**: Secure mark entry and result viewing for staff and students.
- **📨 Feedback & Notifications**: Built-in feedback loop and Firebase-ready notification system.
- **📅 Leave Management**: End-to-end workflow for applying and approving leave requests.

---

## 🏗️ Tech Stack

### Backend
- **Framework**: Django 4.2+ (Python 3.10+)
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Deployment**: Gunicorn + WhiteNoise (Static Files)
- **Database Mapping**: Neon Serverless Postgres

### Frontend
- **Design System**: Editorial Ether (Custom Vanilla CSS + Tailwind-inspired utilities)
- **Typography**: Plus Jakarta Sans, Inter, Manrope
- **Icons**: Material Symbols & Font Awesome
- **Libraries**: Chart.js, jQuery, RTCMultiConnection

---

## 👥 Role-Based Capabilities

### 👑 Owner / Principal / HOD
- Full administrative oversight of students, staff, courses, and subjects.
- Cross-departmental analytics and attendance oversight.
- Management of leave requests (Approve/Reject).
- System-wide notifications and feedback review.

### 👨‍🏫 Staff
- Manage assigned students and track subject-wise attendance.
- Upload/Update student results and internal marks.
- Host live classrooms and interact with students.
- Apply for leaves and submit professional feedback.

### 🎓 Student
- Personalized dashboard with attendance summaries and result tracking.
- Join live classrooms directly from the dashboard.
- View individual results and subject-wise performance.
- Apply for leaves and submit academic feedback.

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/Khush-1911/U-MAS.git
cd U-MAS
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```
Update the `.env` with your `DJANGO_SECRET_KEY` and database credentials.

### 5. Run Migrations & Start Server
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## ☁️ Deployment (Render)

This project is optimized for [Render](https://render.com). It uses `render.yaml` for infrastructure-as-code deployment.

1. Connect your GitHub repository to Render.
2. Render will automatically detect the `render.yaml` file.
3. Configure the following Environment Variables in Render:
   - `DATABASE_URL`: Your Neon PostgreSQL connection string.
   - `DJANGO_SECRET_KEY`: A secure random string.
   - `RECAPTCHA_SITE_KEY` & `RECAPTCHA_SECRET_KEY`: For login security.

---

## 🛡️ Security
- **reCAPTCHA v3**: Integrated into the login flow to prevent bot attacks.
- **Middleware Protection**: Custom role-based access control (RBAC) via `LoginCheckMiddleWare`.
- **Environment Isolation**: Sensitive credentials are never hardcoded.

---

## 📝 Recent Updates
- [x] Complete UI overhaul to **Editorial Ether** design system.
- [x] Integration with Neon PostgreSQL for serverless scaling.
- [x] Refined Staff/Student management with bulk action support.
- [x] Enhanced responsive sidebar and glassmorphism components.

---

Developed with ❤️ by [Khush-1911](https://github.com/Khush-1911)
