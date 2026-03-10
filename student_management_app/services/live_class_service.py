import json
from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.core import signing
from django.utils import timezone

from student_management_app.models import (
    Courses,
    LiveClassParticipant,
    OnlineClassRoom,
    SessionYearModel,
    Staffs,
    Students,
    Subjects,
)


class LiveClassError(Exception):
    pass


def _build_room_value():
    return datetime.now().strftime("%Y%m-%d%H-%M%S-") + str(uuid4())


def create_or_get_active_room(staff_user, subject_id, session_year_id):
    subject_obj = Subjects.objects.get(id=subject_id)
    if subject_obj.staff_id_id != staff_user.id:
        raise LiveClassError("This subject is not assigned to the logged-in staff")
    session_obj = SessionYearModel.object.get(id=session_year_id)
    staff_obj = Staffs.objects.get(admin=staff_user.id)

    existing = OnlineClassRoom.objects.filter(
        subject=subject_obj,
        session_years=session_obj,
        is_active=True,
    ).first()
    if existing:
        if not existing.realtime_room_id:
            existing.realtime_room_id = existing.room_name
            existing.save(update_fields=["realtime_room_id"])
        return existing

    room_pwd = _build_room_value()
    room_name = _build_room_value()
    room = OnlineClassRoom(
        room_name=room_name,
        room_pwd=room_pwd,
        realtime_room_id=room_name,
        subject=subject_obj,
        session_years=session_obj,
        started_by=staff_obj,
        is_active=True,
        status="ACTIVE",
    )
    room.save()
    return room


def validate_student_can_join(student_user, room):
    if not room.is_active or room.status != "ACTIVE":
        raise LiveClassError("Class room is not active")

    student_obj = Students.objects.get(admin=student_user.id)
    subject_course = Courses.objects.get(id=room.subject.course_id.id)
    if student_obj.course_id.id != subject_course.id:
        raise LiveClassError("This subject is not assigned to the student")
    if student_obj.session_year_id.id != room.session_years.id:
        raise LiveClassError("This session is not assigned to the student")
    if student_obj.assigned_staff_id and student_obj.assigned_staff_id != room.started_by_id:
        raise LiveClassError("This class is not assigned to the student")
    return True


def issue_realtime_token(user, room, role, expires_in=300):
    payload = {
        "uid": user.id,
        "rid": room.id,
        "role": role,
        "exp": expires_in,
    }
    return signing.dumps(
        payload,
        salt="live-class-token",
        key=settings.LIVE_TOKEN_SECRET,
    )


def mark_participant_joined(user, room, role, is_publisher=False):
    return LiveClassParticipant.objects.create(
        room=room,
        user=user,
        role=role,
        is_publisher=is_publisher,
    )


def end_room(staff_user, room):
    staff_obj = Staffs.objects.get(admin=staff_user.id)
    room.status = "ENDED"
    room.is_active = False
    room.ended_at = timezone.now()
    room.ended_by = staff_obj
    room.save(update_fields=["status", "is_active", "ended_at", "ended_by"])
    return room


def serialize_room_state(room):
    active_participants = room.participants.filter(left_at__isnull=True).count()
    return {
        "room_id": room.id,
        "realtime_room_id": room.realtime_room_id or room.room_name,
        "status": room.status,
        "is_active": room.is_active,
        "subject_id": room.subject_id,
        "session_year_id": room.session_years_id,
        "active_participants": active_participants,
        "snapshot": json.loads(room.last_board_snapshot) if room.last_board_snapshot else None,
    }
