from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Institution(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    def __str__(self):
        return self.name

class SemesterModel(models.Model):
    id=models.AutoField(primary_key=True)
    semester_start_date=models.DateField()
    semester_end_date=models.DateField()
    object=models.Manager()

class CustomUser(AbstractUser):
    user_type_data=(("1","Owner"),("2","Staff"),("3","Student"),("4","Superuser"),("5","Principal"),("6","College Admin"),("7","HOD"))
    user_type=models.CharField(default="1",choices=user_type_data,max_length=10)
    email = models.EmailField(unique=True)
    notification_email = models.EmailField(blank=True, default="")
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] # Keep username for compatibility but it will mirror email

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
            # Ensure username mirrors email for internal Django usage
            self.username = self.email
        
        if str(self.user_type) == "1":
            self.is_superuser = True
        
        if self.notification_email:
            self.notification_email = self.notification_email.strip().lower()
        elif self.email:
            self.notification_email = self.email
        super().save(*args, **kwargs)

class OwnerProfile(models.Model): # Replaces OwnerProfile
    id=models.AutoField(primary_key=True)
    admin=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    profile_id=models.CharField(max_length=20, unique=True, default="", blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

class Principal(models.Model):
    id=models.AutoField(primary_key=True)
    admin=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    profile_id=models.CharField(max_length=20, unique=True, default="", blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

class CollegeAdmin(models.Model):
    id=models.AutoField(primary_key=True)
    admin=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    profile_id=models.CharField(max_length=20, unique=True, default="", blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

class Department(models.Model): # Replaces Department
    id=models.AutoField(primary_key=True)
    department_name=models.CharField(max_length=255)
    institution=models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

class HOD(models.Model):
    id=models.AutoField(primary_key=True)
    admin=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    department=models.OneToOneField(Department, on_delete=models.CASCADE, null=True, blank=True)
    profile_id=models.CharField(max_length=20, unique=True, default="", blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

class ClassModel(models.Model):
    id = models.AutoField(primary_key=True)
    class_name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.ForeignKey(SemesterModel, on_delete=models.CASCADE)
    total_students = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

class Staffs(models.Model):
    id=models.AutoField(primary_key=True)
    admin=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    profile_id=models.CharField(max_length=20, unique=True, default="", blank=True)
    address=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    fcm_token=models.TextField(default="")
    objects=models.Manager()

class Subjects(models.Model):
    id=models.AutoField(primary_key=True)
    subject_name=models.CharField(max_length=255)
    class_id=models.ForeignKey(ClassModel,on_delete=models.CASCADE, null=True, blank=True)
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
    class_id=models.ForeignKey(ClassModel,on_delete=models.DO_NOTHING, null=True, blank=True)
    semester_id=models.ForeignKey(SemesterModel,on_delete=models.CASCADE, null=True, blank=True)
    mentor=models.ForeignKey(
        Staffs,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mentees",
    )
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    fcm_token=models.TextField(default="")
    objects = models.Manager()

class Attendance(models.Model):
    id=models.AutoField(primary_key=True)
    class_id=models.ForeignKey(ClassModel,on_delete=models.CASCADE, null=True, blank=True)
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
    grade_letter=models.CharField(max_length=10, default="")
    created_at=models.DateField(auto_now_add=True)
    updated_at=models.DateField(auto_now_add=True)
    objects=models.Manager()

class Timetable(models.Model):
    id = models.AutoField(primary_key=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    class_id = models.ForeignKey(ClassModel, on_delete=models.CASCADE)
    semester = models.ForeignKey(SemesterModel, on_delete=models.CASCADE)
    timetable_file = models.FileField(upload_to='timetables/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

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
        if str(instance.user_type)=="1":
            profile = OwnerProfile.objects.create(admin=instance)
            profile.profile_id = f"OWN{profile.id:05d}"
            profile.save(update_fields=["profile_id"])
        elif str(instance.user_type)=="5":
            profile = Principal.objects.create(admin=instance)
            profile.profile_id = f"PRN{profile.id:05d}"
            profile.save(update_fields=["profile_id"])
        elif str(instance.user_type)=="6":
            profile = CollegeAdmin.objects.create(admin=instance)
            profile.profile_id = f"CAD{profile.id:05d}"
            profile.save(update_fields=["profile_id"])
        elif str(instance.user_type)=="7":
            profile = HOD.objects.create(admin=instance)
            profile.profile_id = f"HOD{profile.id:05d}"
            profile.save(update_fields=["profile_id"])
        elif str(instance.user_type)=="2":
            staff = Staffs.objects.create(admin=instance,address="")
            staff.profile_id = f"STF{staff.id:05d}"
            staff.save(update_fields=["profile_id"])
        elif str(instance.user_type)=="3":
            student = Students.objects.create(
                admin=instance,
                address="",
                gender="",
                mentor=None,
            )
            student.profile_id = f"STD{student.id:05d}"
            student.save(update_fields=["profile_id"])

@receiver(post_save,sender=CustomUser)
def save_user_profile(sender,instance,**kwargs):
    try:
        if str(instance.user_type)=="1":
            instance.ownerprofile.save()
        elif str(instance.user_type)=="5":
            instance.principal.save()
        elif str(instance.user_type)=="6":
            instance.collegeadmin.save()
        elif str(instance.user_type)=="7":
            instance.hod.save()
        elif str(instance.user_type)=="2":
            instance.staffs.save()
        elif str(instance.user_type)=="3":
            instance.students.save()
    except Exception:
        pass
