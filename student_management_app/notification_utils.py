from django.conf import settings
from django.core.mail import send_mail

from student_management_app.models import NotificationStudent


def create_student_notifications(students, *, sender_name, title, message):
    notifications = [
        NotificationStudent(
            student_id=student,
            sender_name=sender_name,
            title=title,
            message=message,
        )
        for student in students
    ]
    if notifications:
        NotificationStudent.objects.bulk_create(notifications)
    return len(notifications)


def send_student_notification_emails(students, *, sender_name, title, message):
    recipients = []
    for student in students:
        email = (getattr(student.admin, "email", "") or "").strip()
        if email:
            recipients.append(email)

    if not recipients:
        return 0

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "no-reply@u-mas.local"
    email_body = "\n\n".join(
        [
            f"Sent by {sender_name}",
            f"Title: {title}",
            message,
            "This notification is also available in the U-MAS app.",
        ]
    )
    return send_mail(
        subject=title,
        message=email_body,
        from_email=from_email,
        recipient_list=recipients,
        fail_silently=False,
    )
