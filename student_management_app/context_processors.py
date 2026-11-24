from student_management_app.models import (
    HOD,
    NotificationHOD,
    NotificationStaffs,
    NotificationStudent,
    Staffs,
    Students,
)


def student_notification_badge(request):
    unread_count = 0
    latest_unread_notification_id = None
    latest_unread_sender_name = ""
    staff_unread_count = 0
    hod_unread_count = 0

    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False):
        user_type = str(getattr(user, "user_type", ""))
        if user_type == "3":
            student_id = Students.objects.filter(admin=user.id).values_list("id", flat=True).first()
            if student_id:
                unread_notifications = NotificationStudent.objects.filter(
                    student_id=student_id,
                    is_read=False,
                )
                unread_count = unread_notifications.count()
                latest_unread = unread_notifications.order_by("-created_at").values(
                    "id",
                    "sender_name",
                ).first()
                if latest_unread:
                    latest_unread_notification_id = latest_unread["id"]
                    latest_unread_sender_name = latest_unread["sender_name"]
        elif user_type == "2":
            staff_id = Staffs.objects.filter(admin=user.id).values_list("id", flat=True).first()
            if staff_id:
                staff_unread_count = NotificationStaffs.objects.filter(
                    staff_id=staff_id,
                    is_read=False,
                ).count()
        elif user_type == "7":
            hod_id = HOD.objects.filter(admin=user.id).values_list("id", flat=True).first()
            if hod_id:
                hod_unread_count = NotificationHOD.objects.filter(
                    hod_id=hod_id,
                    is_read=False,
                ).count()

    return {
        "student_unread_notification_count": unread_count,
        "student_latest_unread_notification_id": latest_unread_notification_id,
        "student_latest_unread_sender_name": latest_unread_sender_name,
        "staff_unread_notification_count": staff_unread_count,
        "hod_unread_notification_count": hod_unread_count,
    }
