from student_management_app.models import NotificationStudent, Students


def student_notification_badge(request):
    unread_count = 0
    latest_unread_notification_id = None
    latest_unread_sender_name = ""

    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False) and str(getattr(user, "user_type", "")) == "3":
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

    return {
        "student_unread_notification_count": unread_count,
        "student_latest_unread_notification_id": latest_unread_notification_id,
        "student_latest_unread_sender_name": latest_unread_sender_name,
    }
