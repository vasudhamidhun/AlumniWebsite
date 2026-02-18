from django import forms
from .models import *
import re
class RegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': ' '}),
        label="Confirm Password"
    )

    class Meta:
        model = RegisterModel
        fields = ['username', 'college_id', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': ' '}),
            'college_id': forms.TextInput(attrs={'placeholder': ' '}),
            'email': forms.EmailInput(attrs={'placeholder': ' '}),
            'password': forms.PasswordInput(attrs={'placeholder': ' '}),
        }


    def clean_password(self):
        password = self.cleaned_data.get('password')

        # 🔐 Password Regex:
        # At least 8 characters
        # At least one uppercase letter
        # At least one special character
        pattern = r'^(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{8,}$'

        if not re.match(pattern, password):
            raise forms.ValidationError(
                "Password must be at least 8 characters long, "
                "contain at least one uppercase letter and one special character."
            )

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['staff_id', 'staff_name']
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['username', 'college_id','start_year','end_year']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Enter student username'
            }),
            'college_id': forms.TextInput(attrs={
                'placeholder': 'Enter college ID'
            }),
            'start_year': forms.NumberInput(attrs={
                'placeholder': 'Enter start year (e.g. 2022)'
            }),
            'end_year': forms.NumberInput(attrs={
                'placeholder': 'Enter end year (e.g. 2026)'
            }),


        }

class AlumniProfileForm(forms.ModelForm):
    class Meta:
        model = AlumniProfile
        exclude = ['user']


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        exclude = ['user']


class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        exclude = ['user']

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'event_datetime', 'file']
        widgets = {
            'event_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }

class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ['image', 'description']


class AlumniPostForm(forms.ModelForm):
    class Meta:
        model = AlumniPost
        fields = ['caption', 'image']

class FundraisingForm(forms.ModelForm):
    class Meta:
        model = Fundraising
        fields = ['title', 'description', 'goal_amount', 'donor_name', 'image']


class JobVacancyForm(forms.ModelForm):
    class Meta:
        model = JobVacancy
        fields = [
            'title', 'company_name', 'job_type', 'location',
            'salary', 'description', 'requirements',
            'vacancy_image', 'deadline'
        ]

