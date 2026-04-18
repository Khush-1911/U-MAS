from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Create your models here.
class SemesterModel(models.Model):
    id=models.AutoField(primary_key=True)
    semester_start_date=models.DateField()
    semester_end_date=models.DateField()
    object=models.Manager()

class CustomUser(AbstractUser):
    user_type_data=((1,"HOD"),(2,"Staff"),(3,"Student"))
    user_type=models.CharField(default=1,choices=user_type_data,max_length=10)
    email = models.EmailField(unique=True)
    notification_email = models.EmailField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="customuser_email_ci_unique",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        if self.notification_email:
            self.notification_email = self.notification_email.strip().lower()
        elif self.email:
            self.notification_email = self.email
        super().save(*args, **kwargs)

class AdminHOD(models.Model):
    id=models.AutoField(primary_key=True)
    admin=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    profile_id=models.CharField(max_length=20, unique=True, default="", blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

class Staffs(models.Model):
    id=models.AutoField(primary_key=True)
    admin=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    profile_id=models.CharField(max_length=20, unique=True, default="", blank=True)
    address=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    fcm_token=models.TextField(default="")
    objects=models.Manager()

class Courses(models.Model):
    id=models.AutoField(primary_key=True)
    course_name=models.CharField(max_length=255)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()


class Subjects(models.Model):
    id=models.AutoField(primary_key=True)
    subject_name=models.CharField(max_length=255)
    course_id=models.ForeignKey(Courses,on_delete=models.CASCADE,default=1)
    staff_id=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

class Students(models.Model):
    id=models.AutoField(primary_key=True)
    admin=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    profile_id=models.CharField(max_length=20, unique=True, default="", blank=True)
    gender=models.CharField(max_length=255)
    address=models.TextField()
    course_id=models.ForeignKey(Courses,on_delete=models.DO_NOTHING)
    semester_id=models.ForeignKey(SemesterModel,on_delete=models.CASCADE)
    assigned_staff=models.ForeignKey(
        Staffs,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_students",
    )
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    fcm_token=models.TextField(default="")
    objects = models.Manager()

class Attendance(models.Model):
    id=models.AutoField(primary_key=True)
    subject_id=models.ForeignKey(Subjects,on_delete=models.DO_NOTHING)
    attendance_date=models.DateField()
    created_at=models.DateTimeField(auto_now_add=True)
    semester_id=models.ForeignKey(SemesterModel,on_delete=models.CASCADE)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subject_id", "attendance_date"],
                name="attendance_unique_subject_date",
            ),
        ]

class AttendanceReport(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.DO_NOTHING)
    attendance_id=models.ForeignKey(Attendance,on_delete=models.CASCADE)
    status=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

class LeaveReportStudent(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.CASCADE)
    leave_date=models.CharField(max_length=255)
    leave_message=models.TextField()
    leave_status=models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

class LeaveReportStaff(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    leave_date = models.CharField(max_length=255)
    leave_message = models.TextField()
    leave_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class FeedBackStudent(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    staff_id = models.ForeignKey(
        Staffs,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_feedback_messages",
    )
    feedback = models.TextField()
    feedback_reply = models.TextField(blank=True, default="")
    hod_reply = models.TextField(blank=True, default="")
    forwarded_to_hod = models.BooleanField(default=False)
    forwarded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class FeedBackStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply=models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class NotificationStudent(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    sender_name = models.CharField(max_length=255, default="HOD")
    title = models.CharField(max_length=255, default="Notification")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class NotificationStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    sender_name = models.CharField(max_length=255, default="HOD")
    title = models.CharField(max_length=255, default="Notification")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

class StudentResult(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.CASCADE)
    subject_id=models.ForeignKey(Subjects,on_delete=models.CASCADE)
    subject_exam_marks=models.FloatField(default=0)
    subject_assignment_marks=models.FloatField(default=0)
    created_at=models.DateField(auto_now_add=True)
    updated_at=models.DateField(auto_now_add=True)
    objects=models.Manager()

class OnlineClassRoom(models.Model):
    status_choices = (
        ("ACTIVE", "ACTIVE"),
        ("ENDED", "ENDED"),
    )
    id=models.AutoField(primary_key=True)
    room_name=models.CharField(max_length=255)
    room_pwd=models.CharField(max_length=255)
    realtime_room_id=models.CharField(max_length=255, unique=True, null=True, blank=True)
    subject=models.ForeignKey(Subjects,on_delete=models.CASCADE)
    semester=models.ForeignKey(SemesterModel,on_delete=models.CASCADE)
    started_by=models.ForeignKey(Staffs,on_delete=models.CASCADE)
    is_active=models.BooleanField(default=True)
    status=models.CharField(max_length=16, choices=status_choices, default="ACTIVE")
    ended_at=models.DateTimeField(null=True, blank=True)
    ended_by=models.ForeignKey(Staffs,on_delete=models.SET_NULL,null=True, blank=True, related_name="ended_live_classes")
    created_on=models.DateTimeField(auto_now_add=True)
    last_board_snapshot=models.TextField(null=True, blank=True)
    objects=models.Manager()

class LiveClassParticipant(models.Model):
    role_choices = (
        ("STAFF", "STAFF"),
        ("STUDENT", "STUDENT"),
    )

    id=models.AutoField(primary_key=True)
    room=models.ForeignKey(OnlineClassRoom,on_delete=models.CASCADE, related_name="participants")
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    role=models.CharField(max_length=16, choices=role_choices)
    joined_at=models.DateTimeField(auto_now_add=True)
    left_at=models.DateTimeField(null=True, blank=True)
    is_publisher=models.BooleanField(default=False)
    objects=models.Manager()

    class Meta:
        indexes = [
            models.Index(fields=["room", "role"], name="live_room_role_idx"),
            models.Index(fields=["user", "joined_at"], name="live_user_joined_idx"),
        ]


@receiver(post_save,sender=CustomUser)
def create_user_profile(sender,instance,created,**kwargs):
    if created:
        if instance.user_type==1:
            hod = AdminHOD.objects.create(admin=instance)
            hod.profile_id = f"HOD{hod.id:05d}"
            hod.save(update_fields=["profile_id"])
        if instance.user_type==2:
            staff = Staffs.objects.create(admin=instance,address="")
            staff.profile_id = f"STF{staff.id:05d}"
            staff.save(update_fields=["profile_id"])
        if instance.user_type==3:
            course = Courses.objects.order_by("id").first()
            if course is None:
                course = Courses.objects.create(course_name="Unassigned Course")

            semester = SemesterModel.object.order_by("id").first()
            if semester is None:
                year = timezone.now().date().year
                semester = SemesterModel.object.create(
                    semester_start_date=f"{year}-01-01",
                    semester_end_date=f"{year}-12-31",
                )

            student = Students.objects.create(
                admin=instance,
                course_id=course,
                semester_id=semester,
                address="",
                gender="",
                assigned_staff=None,
            )
            student.profile_id = f"STD{student.id:05d}"
            student.save(update_fields=["profile_id"])

@receiver(post_save,sender=CustomUser)
def save_user_profile(sender,instance,**kwargs):
    if instance.user_type==1:
        instance.adminhod.save()
    if instance.user_type==2:
        instance.staffs.save()
    if instance.user_type==3:
        instance.students.save()
