from django import forms
from django.forms import ChoiceField

from student_management_app.models import Department, SemesterModel, Staffs, Subjects, ClassModel


def _semester_label(semester):
    return (
        f"{semester.semester_start_date.strftime('%d-%m-%Y')} TO "
        f"{semester.semester_end_date.strftime('%d-%m-%Y')}"
    )

class ChoiceNoValidation(ChoiceField):
    def validate(self, value):
        pass

class DateInput(forms.DateInput):
    input_type = "date"

class AddStudentForm(forms.Form):
    email=forms.EmailField(label="Email",max_length=50,widget=forms.EmailInput(attrs={"class":"form-control","autocomplete":"off"}))
    notification_email=forms.EmailField(label="Notification Email",max_length=50,required=False,widget=forms.EmailInput(attrs={"class":"form-control","autocomplete":"off","placeholder":"Optional: defaults to login email"}))
    password=forms.CharField(label="Password",max_length=50,widget=forms.PasswordInput(attrs={"class":"form-control"}))
    first_name=forms.CharField(label="First Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name=forms.CharField(label="Last Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    username=forms.CharField(label="Username",max_length=50,widget=forms.TextInput(attrs={"class":"form-control","autocomplete":"off"}))
    address=forms.CharField(label="Address",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    gender_choice=(
        ("Male","Male"),
        ("Female","Female")
    )

    class_id=forms.ChoiceField(label="Class",choices=[],widget=forms.Select(attrs={"class":"form-control"}))
    sex=forms.ChoiceField(label="Sex",choices=gender_choice,widget=forms.Select(attrs={"class":"form-control"}))
    semester_id=forms.ChoiceField(label="Semester",choices=[],widget=forms.Select(attrs={"class":"form-control"}))
    mentor=forms.ChoiceField(label="Assigned Staff",choices=[],widget=forms.Select(attrs={"class":"form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_id"].choices = [
            (cls.id, cls.class_name) for cls in ClassModel.objects.all()
        ]
        self.fields["semester_id"].choices = [
            (semester.id, _semester_label(semester))
            for semester in SemesterModel.object.all()
        ]
        self.fields["mentor"].choices = [
            (staff.id, f"{staff.profile_id or staff.id} - {staff.admin.get_full_name() or staff.admin.username}")
            for staff in Staffs.objects.select_related("admin").all()
        ]

class EditStudentForm(forms.Form):
    email=forms.EmailField(label="Email",max_length=50,widget=forms.EmailInput(attrs={"class":"form-control"}))
    notification_email=forms.EmailField(label="Notification Email",max_length=50,required=False,widget=forms.EmailInput(attrs={"class":"form-control","placeholder":"Optional: defaults to login email"}))
    first_name=forms.CharField(label="First Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name=forms.CharField(label="Last Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    username=forms.CharField(label="Username",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    address=forms.CharField(label="Address",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))


    gender_choice=(
        ("Male","Male"),
        ("Female","Female")
    )

    class_id=forms.ChoiceField(label="Class",choices=[],widget=forms.Select(attrs={"class":"form-control"}))
    sex=forms.ChoiceField(label="Sex",choices=gender_choice,widget=forms.Select(attrs={"class":"form-control"}))
    semester_id=forms.ChoiceField(label="Semester",choices=[],widget=forms.Select(attrs={"class":"form-control"}))
    mentor=forms.ChoiceField(label="Assigned Staff",choices=[],widget=forms.Select(attrs={"class":"form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_id"].choices = [
            (cls.id, cls.class_name) for cls in ClassModel.objects.all()
        ]
        self.fields["semester_id"].choices = [
            (semester.id, _semester_label(semester))
            for semester in SemesterModel.object.all()
        ]
        self.fields["mentor"].choices = [
            (staff.id, f"{staff.profile_id or staff.id} - {staff.admin.get_full_name() or staff.admin.username}")
            for staff in Staffs.objects.select_related("admin").all()
        ]


class StaffAddStudentForm(forms.Form):
    email=forms.EmailField(label="Email",max_length=50,widget=forms.EmailInput(attrs={"class":"form-control","autocomplete":"off"}))
    notification_email=forms.EmailField(label="Notification Email",max_length=50,required=False,widget=forms.EmailInput(attrs={"class":"form-control","autocomplete":"off","placeholder":"Optional: defaults to login email"}))
    password=forms.CharField(label="Password",max_length=50,widget=forms.PasswordInput(attrs={"class":"form-control"}))
    first_name=forms.CharField(label="First Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name=forms.CharField(label="Last Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    username=forms.CharField(label="Username",max_length=50,widget=forms.TextInput(attrs={"class":"form-control","autocomplete":"off"}))
    address=forms.CharField(label="Address",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    gender_choice=(
        ("Male","Male"),
        ("Female","Female")
    )
    class_id=forms.ChoiceField(label="Class",choices=[],widget=forms.Select(attrs={"class":"form-control"}))
    sex=forms.ChoiceField(label="Sex",choices=gender_choice,widget=forms.Select(attrs={"class":"form-control"}))
    semester_id=forms.ChoiceField(label="Semester",choices=[],widget=forms.Select(attrs={"class":"form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_id"].choices = [
            (cls.id, cls.class_name) for cls in ClassModel.objects.all()
        ]
        self.fields["semester_id"].choices = [
            (semester.id, _semester_label(semester))
            for semester in SemesterModel.object.all()
        ]


class StaffEditStudentForm(forms.Form):
    email=forms.EmailField(label="Email",max_length=50,widget=forms.EmailInput(attrs={"class":"form-control"}))
    notification_email=forms.EmailField(label="Notification Email",max_length=50,required=False,widget=forms.EmailInput(attrs={"class":"form-control","placeholder":"Optional: defaults to login email"}))
    first_name=forms.CharField(label="First Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name=forms.CharField(label="Last Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    username=forms.CharField(label="Username",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    address=forms.CharField(label="Address",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    gender_choice=(
        ("Male","Male"),
        ("Female","Female")
    )
    class_id=forms.ChoiceField(label="Class",choices=[],widget=forms.Select(attrs={"class":"form-control"}))
    sex=forms.ChoiceField(label="Sex",choices=gender_choice,widget=forms.Select(attrs={"class":"form-control"}))
    semester_id=forms.ChoiceField(label="Semester",choices=[],widget=forms.Select(attrs={"class":"form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_id"].choices = [
            (cls.id, cls.class_name) for cls in ClassModel.objects.all()
        ]
        self.fields["semester_id"].choices = [
            (semester.id, _semester_label(semester))
            for semester in SemesterModel.object.all()
        ]

class EditResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.staff_id=kwargs.pop("staff_id")
        super(EditResultForm,self).__init__(*args,**kwargs)
        subject_list=[]
        try:
            subjects=Subjects.objects.filter(staff_id=self.staff_id)
            for subject in subjects:
                subject_single=(subject.id,subject.subject_name)
                subject_list.append(subject_single)
        except:
            subject_list=[]
        self.fields['subject_id'].choices=subject_list

    semester_list=[]
    try:
        semesters=SemesterModel.object.all()
        for semester in semesters:
            semester_single=(semester.id,_semester_label(semester))
            semester_list.append(semester_single)
    except:
        semester_list=[]

    subject_id=forms.ChoiceField(label="Subject",widget=forms.Select(attrs={"class":"form-control"}))
    semester_ids=forms.ChoiceField(label="Semester",choices=semester_list,widget=forms.Select(attrs={"class":"form-control"}))
    student_ids=ChoiceNoValidation(label="Student",widget=forms.Select(attrs={"class":"form-control"}))
    assignment_marks=forms.CharField(label="Assignment Marks",widget=forms.TextInput(attrs={"class":"form-control"}))
    exam_marks=forms.CharField(label="Exam Marks",widget=forms.TextInput(attrs={"class":"form-control"}))
