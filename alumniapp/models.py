from django.contrib import messages
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.models import User

from django.db import models

class Staff(models.Model):
    staff_id = models.CharField(max_length=20, unique=True)
    staff_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.staff_name} ({self.staff_id})"

class Student(models.Model):
    username = models.CharField(max_length=50)
    college_id = models.CharField(max_length=50, unique=True)
    start_year=models.PositiveIntegerField()
    end_year=models.PositiveIntegerField()
    def __str__(self):
        return f"{self.username} ({self.college_id})"

password_validator = RegexValidator(
    regex=r'^(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{8,}$',
    message=(
        'Password must be at least 8 characters long, '
        'contain at least one uppercase letter and one special character.'
    )
)

class PendingRegistration(models.Model):
    username = models.CharField(max_length=50)
    college_id = models.CharField(max_length=50)
    email = models.EmailField()
    password = models.CharField(
        max_length=256,
        validators=[password_validator]
    )
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
class RegisterModel(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('alumni', 'Alumni'),
        ('staff',"Staff")
    )

    username = models.CharField(max_length=50)
    college_id = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=256)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    reset_token = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.role}"


class EmailVerification(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class AlumniProfile(models.Model):
    user = models.OneToOneField(RegisterModel, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    degree = models.CharField(max_length=50, blank=True)
    branch = models.CharField(max_length=50, blank=True)
    batch_year = models.IntegerField(blank=True, null=True)
    current_company = models.CharField(max_length=100, blank=True)
    current_designation = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=50, blank=True)
    skills = models.TextField(blank=True)
    def __str__(self):
        return f"{self.user.username}'s Profile"

class StudentProfile(models.Model):
    user = models.OneToOneField(RegisterModel, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)

    degree = models.CharField(max_length=50)
    branch = models.CharField(max_length=50)
    batch_year = models.IntegerField()
    interests = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} (Student)"
class StaffProfile(models.Model):
    user = models.OneToOneField(RegisterModel, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    contact = models.CharField(max_length=20)
    department = models.CharField(max_length=50)
    subject = models.CharField(max_length=50)
    achievements = models.TextField(blank=True)
    start_year = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} (Staff)"


class Follow(models.Model):
    follower = models.ForeignKey(RegisterModel, on_delete=models.CASCADE,
                                 related_name="following")
    following = models.ForeignKey(RegisterModel, on_delete=models.CASCADE,
                                  related_name="followers")
    class Meta:
        unique_together = ('follower', 'following')






class AlumniPost(models.Model):
    VISIBILITY_CHOICES = (
        ("public", "Visible to all"),
        ("followers", "Visible only to followers"),
    )

    alumni = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="posts"
    )

    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="admin_posts"
    )
    bookmarks = models.ManyToManyField(
        RegisterModel,
        related_name="bookmarked_posts",
        blank=True
    )
    caption = models.TextField(blank=True)
    image = models.ImageField(upload_to="alumni_posts/", null=True, blank=True)
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.admin:
            return f"Admin Post ({self.created_at.date()})"
        if self.alumni:
            return f"{self.alumni.username}'s Post"
        return "Post (No User)"

class PostLike(models.Model):
    user = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)
    post = models.ForeignKey(AlumniPost, on_delete=models.CASCADE,
                             related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'post')
class PostComment(models.Model):
    post = models.ForeignKey(AlumniPost, on_delete=models.CASCADE,
                             related_name="comments")
    user = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Comment by {self.user.username}"



def validate_future_date(value):
    if value <= timezone.now():
        raise ValidationError("Event date must be in the future.")

class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()  # ⬅ Added description field
    event_datetime = models.DateTimeField(validators=[validate_future_date])
    file = models.FileField(upload_to='event_files/')

    def __str__(self):
        return self.name


class Gallery(models.Model):
    image = models.ImageField(upload_to='gallery/')
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description[:50]

class Fundraising(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    raised_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    donor_name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='fundraising_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class JobVacancy(models.Model):
    created_by = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)
    JOB_TYPES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    )

    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    location = models.CharField(max_length=200)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    vacancy_image = models.ImageField(upload_to='job_images/', blank=True, null=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"
from .utils import encrypt_message, decrypt_message

class Message(models.Model):
    sender = models.ForeignKey(
        RegisterModel, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        RegisterModel, on_delete=models.CASCADE, related_name="received_messages"
    )
    encrypted_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def set_message(self, text):
        self.encrypted_text = encrypt_message(text)

    def get_message(self):
        return decrypt_message(self.encrypted_text)

    def __str__(self):
        return f"{self.sender} → {self.receiver}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('post', 'Post'),
        ('job', 'Job'),
        ('follow',"Follow")
    )

    recipient = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name='sent_notifications'
    )

    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(
        AlumniPost,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    job = models.ForeignKey(
        JobVacancy,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}"



