from django.shortcuts import render,redirect, get_object_or_404
from .forms import *
from .utils import send_notification_email
import random
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth.tokens import default_token_generator
from .models import EmailVerification
from django.utils.http import urlsafe_base64_decode
from django.conf import settings
import uuid
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from datetime import *


def index(request):
    return render(request,'index.html')

def adminlogin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        # Always clear previous session
        request.session.flush()

        admin_user = authenticate(username=username, password=password)
        if admin_user is not None and admin_user.is_superuser:
            login(request, admin_user)
            request.session["admin_id"] = admin_user.id
            return redirect("admindash")
    return render(request,'admin/adminlogin.html')



def logout(request):
    request.session.flush()
    return redirect('index')

# ----------------------------------------------admin

def admindash(request):
    from django.utils import timezone
    # get all alumni posts
    posts = AlumniPost.objects.all().order_by('-created_at')
    total_teachers = Staff.objects.count()
    current_year = date.today().year
    print("UTC NOW:", timezone.now())
    print("EVENTS:", Event.objects.all().values('name', 'event_datetime'))
    total_alumni = Student.objects.filter(end_year__lt=current_year).count()
    total_students = Student.objects.filter(end_year__gte=current_year).count()
    registered_teachers = RegisterModel.objects.filter(role='staff').count()
    registered_students = RegisterModel.objects.filter(role='student').count()
    registered_alumni = RegisterModel.objects.filter(role='alumni').count()
    upcoming_events = Event.objects.filter(
        event_datetime__gte=timezone.now()
    ).order_by('event_datetime')[:3]

    return render(request, 'admin/admin_dashboard.html',
                  {'posts': posts,
                   "total_teachers":total_teachers,
                   "total_alumni":total_alumni,
                   "total_students":total_students,
                   "registered_teachers":registered_teachers,
                   "registered_students":registered_students,
                   "registered_alumni":registered_alumni,
                   'events': upcoming_events
})


def delete_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(AlumniPost, id=post_id)

        # ✅ Allow only owner (alumni or admin) to delete
        if (post.alumni and request.user.id == post.alumni.id) or \
           (post.admin and request.user == post.admin):

            post.delete()
            messages.success(request, "Post deleted successfully")
        else:
            messages.error(request, "Not authorized to delete this post")

    return redirect("admindash")
def add_staff(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('staff_list')
    else:
        form = StaffForm()

    return render(request, 'admin/staff_form.html', {'form': form, 'title': 'Add Staff'})

def staff_list(request):
    staffs = Staff.objects.all()
    return render(request, 'admin/staff_list.html', {'staffs': staffs})
def delete_staff(request, id):
    staff = get_object_or_404(Staff, id=id)
    staff.delete()
    return redirect('staff_list')


def update_staff(request, id):
    staff = get_object_or_404(Staff, id=id)

    if request.method == 'POST':
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            return redirect('staff_list')
    else:
        form = StaffForm(instance=staff)

    return render(request, 'admin/staff_form.html', {'form': form, 'title': 'Update Staff'})

def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully!")
            return redirect('add_student')  # redirect to same page after adding
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm()

    return render(request, 'manage/add_student.html', {'form': form})



#----------------------------------------------alumni

def student_register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            student = Student.objects.filter(
                username=data['username'],
                college_id=data['college_id']
            ).first()

            if not student:
                messages.error(request, "No student found with this ID.")
                return render(request, 'student/register.html', {'form': form})

            current_year = datetime.now().year

            if student.end_year < current_year:
                messages.error(
                    request,
                    "You cannot register as Student. Your course is completed."
                )
                return render(request, 'student/register.html', {'form': form})

            token = uuid.uuid4().hex

            PendingRegistration.objects.create(
                username=data['username'],
                college_id=data['college_id'],
                email=data['email'],
                password=make_password(data['password']),
                token=token

            )
            role="student"
            verify_url = request.build_absolute_uri(f"/verify/{token}/{role}")

            send_mail(
                "Verify your Student Account",
                f"Click the link to verify your account:\n{verify_url}",
                "midhunvasudha@gmail.com",
                [data['email']],
            )

            messages.success(
                request,
                "Student registered successfully. Check your email to verify."
            )
            return redirect('student_register')
        else:
            return render(request, 'student/register.html', {'form': form})

    else:
        form = RegisterForm()

    return render(request, 'student/register.html', {'form': form})
def alumni_register(request,role):
    role=role
    print("role :",role)
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            if role=="alumni" or role=="student" :
                student = Student.objects.filter(
                    username=data['username'],
                    college_id=data['college_id']
                ).first()

                if not student:
                    messages.error(request, "No alumni found with this ID.")
                    return render(request, 'alumni/register.html', {'form': form})

                current_year = datetime.now().year

                if student.end_year >= current_year:
                    messages.error(
                        request,
                        "You cannot register as Alumni. You are still a student."
                    )
                    return render(request, 'alumni/register.html', {'form': form})
            else:
                staff = Staff.objects.filter(
                    staff_name=data['username'],
                    staff_id=data['college_id']
                ).first()
                if not staff:
                    messages.error(request, "No staff found with this ID.")
                    return render(request, 'alumni/register.html', {'form': form,"role":role})

            token = uuid.uuid4().hex

            PendingRegistration.objects.create(
                username=data['username'],
                college_id=data['college_id'],
                email=data['email'],
                password=make_password(data['password']),
                token=token

            )
            role=role
            verify_url = request.build_absolute_uri(f"/verify/{token}/{role}")

            send_mail(
                "Verify your Alumni Account",
                f"Click the link to verify your account:\n{verify_url}",
                "midhunvasudha@gmail.com",
                [data['email']],
            )

            messages.success(
                request,
                " registered successfully. Check your email to verify."
            )
            return redirect('alumni_register',role)
        else:

            return render(request, 'alumni/register.html', {'form': form,"role":role})

    else:
        form = RegisterForm()

    return render(request, 'alumni/register.html', {'form': form,"role":role})

def verify_email(request, token,role):
    try:
        pending = PendingRegistration.objects.get(token=token)
    except PendingRegistration.DoesNotExist:
        messages.error(request, "error verification link.")
        if role=="student":

            return redirect("student_register")
        else:
            return redirect("alumni_register",role)

    # Move to real RegisterModel
    if role == "student":
        RegisterModel.objects.create(
            username=pending.username,
            college_id=pending.college_id,
            email=pending.email,
            password=pending.password,
            role='student',
            reset_token=token)
        pending.delete()
        messages.success(request, "Email verified! You can now log in.")
        return redirect("student_login")
    elif role=="alumni":
            RegisterModel.objects.create(
                username=pending.username,
                college_id=pending.college_id,
                email=pending.email,
                password=pending.password,
                role='alumni',
                reset_token=token)
            pending.delete()
            messages.success(request, "Email verified! You can now log in.")
            return redirect("alumni_login")
    else:
        RegisterModel.objects.create(
            username=pending.username,
            college_id=pending.college_id,
            email=pending.email,
            password=pending.password,
            role='staff',
            reset_token=token)
        pending.delete()
        messages.success(request, "Email verified! You can now log in.")
        return redirect("staff_login")
    # return HttpResponse("registered")


def login_view(request, role):
    if request.method == "POST":

        # OTP verification step
        if "otp" in request.POST:
            entered_otp = request.POST.get("otp")

            if entered_otp == request.session.get("login_otp"):
                user_id = request.session.get("otp_user_id")

                # ✅ Remove ONLY OTP-related data
                request.session.pop("login_otp", None)
                request.session.pop("otp_user_id", None)

                # ✅ Set login session
                request.session["user_id"] = user_id
                request.session["role"] = role

                return redirect("dashboard")
            else:
                messages.error(request, "Invalid OTP")

        else:
            username = request.POST.get("username")
            password = request.POST.get("password")

            try:
                user = RegisterModel.objects.get(username=username)

                if check_password(password, user.password):


                    otp = str(random.randint(100000, 999999))
                    request.session["login_otp"] = otp
                    request.session["otp_user_id"] = user.id

                    send_mail(
                        "Login OTP",
                        f"Your OTP is {otp}",
                        "vasudhamadhuramath@gmail.com",
                        [user.email],
                        fail_silently=False,
                    )

                    messages.success(request, "OTP sent to your registered email")

                    return render(request, "alumni/login.html", {
                        "role": role,
                        "show_otp": True,
                        "username": username,
                        "password":password

                    })

                else:
                    messages.error(request, "Incorrect password")

            except RegisterModel.DoesNotExist:
                messages.error(request, "User not found")

    return render(request, "alumni/login.html", {"role": role})

#

def add_comment(request, post_id):
    print("************************comment")
    alumni_id = request.session.get('user_id')
    if not alumni_id:
        return redirect("index")

    user = RegisterModel.objects.get(id=alumni_id)
    post = AlumniPost.objects.get(id=post_id)

    if request.method == "POST":
        comment_text = request.POST.get("comment")

        if comment_text.strip() != "":
            PostComment.objects.create(
                post=post,
                user=user,
                comment=comment_text
            )

    return redirect("dashboard")

def toggle_like(request, post_id):
    alumni_id = request.session.get('user_id')
    role= request.session.get('role')
    if not alumni_id:
        if role=="student":
            return redirect("student_login")
        elif role=="alumni":
            return redirect("alumni_login")
        else:
            return redirect("adminlogin")

    user = RegisterModel.objects.get(id=alumni_id)
    post = AlumniPost.objects.get(id=post_id)

    like, created = PostLike.objects.get_or_create(user=user, post=post)

    if not created:
        # Like already exists → user wants to unlike
        like.delete()

    return redirect("dashboard")


def user_dashboard(request):
    # Check if user is logged in
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id:
        if role == "student":
            return redirect("student_login")
        elif role == "alumni":
            return redirect("alumni_login")
        elif role=="staff":
            return redirect("staff_login")
        else:
            return redirect("adminlogin")

    user = RegisterModel.objects.get(id=user_id)

    # Check if profile exists
    try:
        if role=="alumni":
            profile = AlumniProfile.objects.get(user=user)
            has_profile = True
        elif role=="staff":
            profile = StaffProfile.objects.get(user=user)
            has_profile = True
        else:
            profile = StudentProfile.objects.get(user=user)
            has_profile = True
    except AlumniProfile.DoesNotExist:
        profile = None
        has_profile = False
    except StudentProfile.DoesNotExist:
        profile = None
        has_profile = False
    except StaffProfile.DoesNotExist:
        profile = None
        has_profile = False

    # Get all posts by this user
    posts = AlumniPost.objects.filter(alumni=user).order_by('-created_at')

    # Annotate each post with like info
    for post in posts:
        post.is_liked = PostLike.objects.filter(user=user, post=post).exists()
        post.like_count = post.likes.count()       # Total likes
        post.comments_list = post.comments.all()  # Related comments

    context = {
        'user': user,
        'profile': profile,
        'has_profile': has_profile,
        'posts': posts,
        "role":role
    }
    return render(request, 'alumni/alumni_personal_dash.html', context)
def create_profile(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    print("************create profile *",role)
    if not user_id or not role:
        messages.error(request, "Session expired")
        return redirect('login')
    user = RegisterModel.objects.get(id=user_id)
    # ROLE → FORM & TEMPLATE
    if role == 'alumni':
        FormClass = AlumniProfileForm
    elif role == 'student':
        FormClass = StudentProfileForm
    elif role == 'staff':
        FormClass = StaffProfileForm
    else:
        messages.error(request, "Invalid role")
        return redirect('login')
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, "Profile created successfully!")
            return redirect('user_dashboard')
    else:
        form = FormClass()
        if role=="student":
            return render(request, "profiles/create_student_profile.html", {'form': form, 'role': role})
        elif role=="staff":
            return render(request, "profiles/create_staff_profile.html", {'form': form, 'role': role})
        else:
            return render(request, "alumni/create_profile.html", {'form': form, 'role': role})



def update_profile(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    user = RegisterModel.objects.get(id=user_id)

    # Get existing profile OR create if missing
    if role=="alumni":
        profile, created = AlumniProfile.objects.get_or_create(user=user)
        form=AlumniProfileForm
        template="alumni/create_profile.html"
    elif role=="student":
        profile, created = StudentProfile.objects.get_or_create(user=user)
        form=StudentProfileForm
        template="profiles/create_student_profile.html"
    elif role == "staff":
        profile, created = StaffProfile.objects.get_or_create(user=user)
        form=StaffProfileForm
        template="profiles/create_staff_profile.html"
    if request.method == 'POST':
        form = form(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('user_dashboard')
    else:
        form = form(instance=profile)

    return render(request, template, {'form': form})

# password reset
def send_reset_page(request,role):
    return render(request, "auth/password_reset.html",{"role":role})

def send_reset_email(request,role):
    if request.method != "POST":
        return redirect("password_reset")

    email = request.POST.get('email')

    try:
        user = RegisterModel.objects.get(email=email,role=role)

    except RegisterModel.DoesNotExist:
        messages.error(request, "Email not found!")
        return redirect("password_reset")

    token = str(uuid.uuid4())
    user.reset_token = token
    user.save()

    reset_link = request.build_absolute_uri(f"/reset-password/{user.id}/{token}/")

    send_mail(
        "Reset Your Password",
        f"Click here to reset your password: {reset_link}",
        "midhunvasudha@gmail.com",
        [email]
    )

    messages.success(request, "Reset link sent to your email.")

    if role=="student":
        return redirect("student_login")
    elif role=="alumni":
        return redirect("alumni_login")
    else:
        return redirect("alumni_login")

def custom_reset_confirm(request, uid, token):
    try:
        user = RegisterModel.objects.get(id=uid, reset_token=token)
    except RegisterModel.DoesNotExist:
        messages.error(request, "Invalid reset link!")
        role = request.session.get('role')
        if role == "student":
            return redirect("student_login")
        elif role == "alumni":
            return redirect("alumni_login")

    if request.method == "POST":
        new_pass = request.POST["password"]
        user.password = make_password(new_pass)  # returns hashed strin
        user.reset_token = None  # ✔ Delete token
        user.save()
        messages.success(request, "Password reset successfully!")
        role = request.session.get('role')
        if role == "student":
            return redirect("student_login")
        elif role == "alumni":
            return redirect("alumni_login")

    return render(request, "auth/custom_reset_form.html", {"user": user})

#------alumni search
def alumni_search(request):
    query = request.GET.get('q', '')

    results = []
    if query:
        alumni_results = AlumniProfile.objects.filter(
            Q(user__username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(batch_year__icontains=query) |
            Q(current_company__icontains=query) |
            Q(current_designation__icontains=query) |
            Q(location__icontains=query) |
            Q(skills__icontains=query)
        )

        student_results = StudentProfile.objects.filter(
            Q(user__username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(degree__icontains=query) |
            Q(branch__icontains=query) |
            Q(batch_year__icontains=query) |
            Q(interests__icontains=query)
        )

        staff_results = StaffProfile.objects.filter(
            Q(user__username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(department__icontains=query) |
            Q(subject__icontains=query) |
            Q(achievements__icontains=query) |
            Q(start_year__icontains=query)
        )
    role=request.session.get("role")
    return render(request, "alumni_search.html", {
        "query": query,
        'alumni_results': alumni_results,
        'student_results': student_results,
        'staff_results': staff_results,
        "role":role
    })

def user_profile(request, id):#registermodel id
    profile = RegisterModel.objects.get(id=id)
    user_id=id
    role=profile.role
    if role=="staff":
        user=StaffProfile.objects.get(user=profile)
    elif role=="student":
        user = StudentProfile.objects.get(user=profile)
        print(user)
    else:
        user = AlumniProfile.objects.get(user=profile)
    posts = AlumniPost.objects.filter(
        alumni=profile
    ).order_by("-created_at")

    # check follow status
    is_following = Follow.objects.filter(follower=request.session.get('user_id'),
                                         following=id).exists()

    return render(request, "alumni_profile_page.html", {
        "profile": user,
        "posts": posts,
        "is_following": is_following
    })









def follow_user(request, user_id):
    follower_id = request.session.get("user_id")

    if not follower_id:
        messages.info(request, "Please login first.")
        role = request.session.get('role')
        if role == "student":
            return redirect("student_login")
        elif role == "alumni":
            return redirect("alumni_login")
        else:
            return redirect("staff_login")

    # Prevent self-follow
    if follower_id == user_id:
        messages.warning(request, "You cannot follow yourself.")
        return redirect("user_profile", id=user_id)

    follower = RegisterModel.objects.get(id=follower_id)
    following = RegisterModel.objects.get(id=user_id)

    # Already following check
    if Follow.objects.filter(follower=follower, following=following).exists():
        messages.info(request, "You already follow this user.")
        return redirect("user_profile", id=user_id)

    # Create follow
    Follow.objects.create(follower=follower, following=following)

    # Check if mutual follow already exists
    is_mutual = Follow.objects.filter(
        follower=following,
        following=follower
    ).exists()

    # Notification
    Notification.objects.create(
        recipient=following,
        sender=follower,
        notification_type='follow',
        message=f"{follower.username} started following you"
    )

    # EMAIL
    subject = f"{follower.username} started following you!"
    plain_message = f"{follower.username} started following you."

    html_message = f"""
        <h2>{follower.username} is now following you!</h2>
    """

    # ✅ Show follow-back ONLY if not mutual
    if not is_mutual:
        follow_back_url = request.build_absolute_uri(
            f"/follow-back/{follower.id}/{following.id}/"
        )
        html_message += f"""
            <p>
                <a href="{follow_back_url}"
                   style="padding:10px 15px;background:#0d6efd;color:white;
                   text-decoration:none;border-radius:5px;">
                   Follow Back
                </a>
            </p>
        """
        plain_message += f"\nFollow back: {follow_back_url}"

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [following.email],
            html_message=html_message
        )
    except Exception as e:
        messages.error(request, f"Email could not be sent: {e}")

    messages.success(request, "Followed successfully!")
    return redirect("user_profile", id=user_id)

def follow_back(request, follower_id, following_id):
    """
    follower_id  → user who followed originally
    following_id → user clicking follow-back now
    """
    try:
        original_follower = RegisterModel.objects.get(id=follower_id)
        current_user = RegisterModel.objects.get(id=following_id)
    except RegisterModel.DoesNotExist:
        messages.error(request, "Invalid follow-back link.")
    role = request.session.get("role")

    return redirect("dashboard")
    # Prevent self-follow (should never happen)
    if current_user.id == original_follower.id:
        messages.info(request, "Invalid follow-back request.")
        return redirect("dashboard")

    # Create reverse follow
    Follow.objects.get_or_create(
        follower=current_user,
        following=original_follower
    )

    messages.success(request, "You followed back successfully!")

    return redirect("friends_list")

def friends_list(request):
    alumni_id = request.session.get("user_id")
    if not alumni_id:
        role = request.session.get('role')
        if role == "student":
            return redirect("student_login")
        elif role == "alumni":
            return redirect("alumni_login")
        elif role == "staff":
            return redirect("staff_login")

    user = RegisterModel.objects.get(id=alumni_id)
    role=user.role
    # Users who both follow and are followed
    following_ids = Follow.objects.filter(follower=user).values_list("following",flat=True)
    follower_ids  = Follow.objects.filter(following=user).values_list("follower",flat=True)
    print(f"**********************follow \n {following_ids},\n{follower_ids}")


    mutual_ids = set(following_ids).intersection(set(follower_ids))
    print(f"mutual ids : {mutual_ids}")

    friends = RegisterModel.objects.filter(id__in=mutual_ids)

    return render(request, "friends_list.html", {"friends": friends,"role":role})


def follow_toggle(request, id):
    current_user = RegisterModel.objects.get(id=request.session.get('alumni_id'))
    target = RegisterModel.objects.get(id=id)

    follow, created = Follow.objects.get_or_create(follower=current_user, following=target)

    if not created:   # already following → unfollow
        follow.delete()

    return redirect('alumni_profile', id=id)

def unfollow(request, user_id):
    # logged-in user id from session
    my_id = request.session.get('user_id')

    if not my_id:
        messages.error(request, "Please login first")
        return redirect('login')

    follower = get_object_or_404(RegisterModel, id=my_id)
    following = get_object_or_404(RegisterModel, id=user_id)

    # delete follow relation
    Follow.objects.filter(
        follower=follower,
        following=following
    ).delete()

    messages.success(request, f"You unfollowed {following.username}")
    return redirect('dashboard')


#---------------------------admin function
def add_event(request):
    role=request.session.get('role')
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            messages.success(request, "Event Added successfully!")

            return redirect("add_event")  # Create a success URL/view
        else:
            messages.error(request, "Invalid data.")
            return redirect("add_event")
    else:
        form = EventForm()

    return render(request, "manage/add_event.html", {"form": form,"role":role})
def event_success(request):
    return render(request, "manage/event_success.html")


def view_all_events(request):
    # Get all events ordered by datetime (upcoming first)
    events = Event.objects.all().order_by('event_datetime')
    role=request.session.get("role")
    return render(request, 'viewall_event.html', {'events': events,"role":role})
def add_gallery(request):
    role = request.session.get("role")
    if request.method == "POST":

        form = GalleryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Image added to gallery!")
            return redirect('add_gallery')
    else:
        form = GalleryForm()

    return render(request, 'manage/add_gallery.html', {'form': form,"role":role})

def gallery_list(request):
    images = Gallery.objects.order_by('-created_at')
    role = request.session.get("role")
    return render(request, 'manage/gallery_list.html', {'images': images,"role":role})



from django.contrib.auth.models import User

def add_post(request):
    role = request.session.get("role")

    post_user = None
    is_admin = False

    # 1️⃣ Admin user
    if not role:
        post_user = request.user
        is_admin = True
        print("iam admin-------------------------------------")

    # 2️⃣ Alumni user
    else:
        alumni_id = request.session.get("user_id")
        if not alumni_id:
            messages.error(request, "Please login first.")
            return redirect("alumni_login")

        post_user = RegisterModel.objects.get(id=alumni_id)

    # 3️⃣ Save Post
    if request.method == "POST":
        caption = request.POST.get("caption")
        image = request.FILES.get("image")

        post = AlumniPost(
            caption=caption,
            image=image,
            visibility="public" if is_admin else "followers"
        )

        if is_admin:
            post.admin = post_user
        else:
            post.alumni = post_user

        post.save()
        notify_followers(
            sender=post_user,
            notification_type='post',
            post=post
        )

        # messages.success(request, "Post added successfully!")
        return redirect("dashboard")
        if is_admin:
            return redirect("admindash")
        else:
            return redirect("dashboard")

    form = AlumniPostForm()
    return render(request, "manage/add_post.html", {"form": form,"role":role})



def bookmark(request,id):
    post = get_object_or_404(AlumniPost, id=id)
    user_id = request.session.get("user_id")
    user=RegisterModel.objects.get(id=user_id)

    if user in post.bookmarks.all():
        post.bookmarks.remove(user)
    else:
        post.bookmarks.add(user)

    return redirect(request.META.get("HTTP_REFERER", "/"))
def delete_post(request,id):
    post=AlumniPost.objects.get(id=id)
    post.delete()
    messages.success(request,"Post delete")
    return redirect("user_dashboard")

def bookmarked_posts(request):
    user_id = request.session.get("user_id")
    user = RegisterModel.objects.get(id=user_id)
    posts = AlumniPost.objects.filter(bookmarks=user).order_by("-created_at")
    return render(request, "manage/bookmarked_posts.html", {"posts": posts})
def fundraising_create(request):
    role=request.session.get("role")
    if request.method == "POST":
        form = FundraisingForm(request.POST, request.FILES)  # <-- Add request.FILES
        if form.is_valid():
            form.save()
            return redirect("fundraising_list")
    else:
        form = FundraisingForm()

    return render(request, "manage/fundraising_create.html", {"form": form,"role":role})

def fundraising_list(request):
    role = request.session.get("role")
    fundraisings = Fundraising.objects.all().order_by("-created_at")
    return render(request, "manage/fundraising_list.html", {"fundraisings": fundraisings,"role":role})

def job_create(request):

    # get logged-in user from session
    alumni_id = request.session.get('user_id')
    role = request.session.get('role')
    if not alumni_id:
        messages.info(request, "Your session has expired. Please login again.")

        if role == "student":
            return redirect("student_login")
        elif role == "alumni":
            return redirect("alumni_login")
        else:
            return redirect("adminlogin")

    user = RegisterModel.objects.get(id=alumni_id)

    if request.method == "POST":
        form = JobVacancyForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = user       # <-- IMPORTANT
            job.save()
            notify_followers(
                sender=user,
                notification_type='job',
                job=job
            )
            return redirect('jobs_from_following')
    else:
        form = JobVacancyForm()

    return render(request, 'manage/job_create.html', {'form': form, 'user': user,"role":role})
def jobs_from_following(request):

    # Get logged-in user from session
    alumni_id = request.session.get('user_id')
    if not alumni_id:
        messages.info(request, "Your session has expired. Please login again.")
        role = request.session.get('role')
        if role == "student":
            return redirect("student_login")
        elif role == "alumni":
            return redirect("alumni_login")
        else:
            return redirect("adminlogin")

    user = RegisterModel.objects.get(id=alumni_id)
    role=user.role
    # get users I am following
    following_users = Follow.objects.filter(follower=user)\
        .values_list('following_id', flat=True)

    # get jobs posted by followed users
    jobs = JobVacancy.objects.filter(created_by__in=following_users)

    return render(request, "manage/jobs_following.html", {
        "user": user,
        "jobs": jobs,
        "role":role
    })

def messages_dashboard(request):
    alumni_id = request.session.get("user_id")
    if not alumni_id:
        role = request.session.get('role')
        if role == "student":
            return redirect("student_login")
        elif role == "alumni":
            return redirect("alumni_login")
        elif role == "staff":
            return redirect("staff_login")

    user = RegisterModel.objects.get(id=alumni_id)

    friends = RegisterModel.objects.filter(
        followers__follower=user,   # users who follow me
        following__following=user   # users I follow
    ).exclude(id=user.id).distinct()

    print("FRIENDS FOUND:", list(friends.values_list("id", flat=True)))

    return render(request, "messages/dashboard.html", {
        "friends": friends
    })

def chat_view(request, follower_id):
    user_id = request.session.get('user_id')
    current_user = RegisterModel.objects.get(id=user_id)
    follower = RegisterModel.objects.get(id=follower_id)

    messages = Message.objects.filter(
        sender__in=[current_user, follower],
        receiver__in=[current_user, follower]
    ).order_by('timestamp')

    # ✅ MARK RECEIVED MESSAGES AS READ
    Message.objects.filter(
        sender=follower,
        receiver=current_user,
        is_read=False
    ).update(is_read=True)

    # decrypt messages
    for msg in messages:
        msg.text = msg.get_message()

    return render(request, 'messages/chat.html', {
        'follower': follower,
        'messages': messages
    })
def send_message(request, follower_id):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        sender = RegisterModel.objects.get(id=user_id)
        receiver = RegisterModel.objects.get(id=follower_id)

        text = request.POST.get('message')

        msg = Message(sender=sender, receiver=receiver)
        msg.set_message(text)
        msg.save()

    return redirect('chat', follower_id=follower_id)
def ajax_search_friends(request):
    alumni_id = request.session.get('alumni_id')
    if not alumni_id:
        return JsonResponse({"results": []})

    user = RegisterModel.objects.get(id=alumni_id)
    query = request.GET.get('q', '').strip()

    following_ids = Follow.objects.filter(follower=user).values_list("following", flat=True)
    follower_ids = Follow.objects.filter(following=user).values_list("follower", flat=True)
    mutual_ids = set(following_ids).intersection(set(follower_ids))

    friends = RegisterModel.objects.filter(id__in=mutual_ids)
    if query:
        friends = friends.filter(username__icontains=query)

    results = [{"id": f.id, "username": f.username} for f in friends]

    return JsonResponse({"results": results})

def notify_followers(sender, notification_type, post=None, job=None):
    print(f"sender : {sender} ")
    followers = Follow.objects.filter(following=sender)

    for f in followers:
        recipient = f.follower

        if notification_type == 'post':
            message = f"{sender.username} added a new post"
            subject = "New Post from someone you follow"
        else:
            message = f"{sender.username} posted a new job"
            subject = "New Job Opportunity"

        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            post=post,
            job=job,
            message=message
        )

        # 📧 Email
        if recipient.email:
            send_notification_email(subject, message, recipient.email)


def notification_count(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return {}

    count = Notification.objects.filter(
        recipient_id=user_id,
        is_read=False
    ).count()

    return {'notification_count': count}

def notifications(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id:
        messages.error(request, "Please login again.")
        return redirect("alumni_login")

    notifications = Notification.objects.filter(
        recipient_id=user_id
    ).order_by("-created_at")

    # ✅ Mark all as read
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, "notifications.html", {
        "notifications": notifications,
        "role": role,
    })
# “We implemented an AI-inspired recommendation system
# using similarity matching on alumni attributes like
# batch, location, company and skills, while
# excluding already followed users. This mimics
# LinkedIn’s ‘People You May Know’ feature.”


def dashboard(request):
    alumni_id = request.session.get('user_id')
    role = request.session.get("role")
    recommended_alumni = []  # ✅ ALWAYS define
    recommended_students = []
    recommended_staffs = []
    if not alumni_id:
        messages.info(request, "Your session has expired. Please login again.")
        return redirect('index')

    user = RegisterModel.objects.get(id=alumni_id)
    profile_exists = True
    print(user.role,user.username)
    if role=="alumni":
        profile = AlumniProfile.objects.filter(user=user).first()
        suggestions = AlumniProfile.objects.none()

        profile_exists = hasattr(user, "alumniprofile")
    elif role=="student":
        profile = StudentProfile.objects.filter(user=user).first()
        suggestions = StudentProfile.objects.none()
        profile_exists = hasattr(user, "studentprofile")
    elif role=="staff":
        profile = StaffProfile.objects.filter(user=user).first()
        suggestions = StaffProfile.objects.none()
        profile_exists = hasattr(user, "staffprofile")

    following_users = Follow.objects.filter(
        follower=user
    ).values_list("following_id", flat=True)

    posts = (
        AlumniPost.objects.filter(
            # 1️⃣ Admin public posts
            Q(admin__isnull=False, visibility="public")

            |

            # 2️⃣ Followers' alumni posts
            Q(alumni__id__in=following_users, visibility="followers")
            |
            Q(alumni=user)
        )
          # ❌ exclude own posts
        .select_related("admin", "alumni", "alumni__alumniprofile")
        .prefetch_related("likes", "comments")
        .order_by("-created_at")
    )

    for post in posts:
        post.is_liked = PostLike.objects.filter(user=user, post=post).exists()

    # ================= AI SUGGESTIONS =================
    # suggestions = AlumniProfile.objects.none()

    if profile:



        data=AlumniProfile.objects.all()
        recommended = recommend_alumni(data,profile.id)

        # Fetch actual objects
        # alumni_ids = [r["profile_id"] for r in recommended if r["role"] == "alumni"]
        # student_ids = [r["profile_id"] for r in recommended if r["role"] == "student"]
        # staff_ids = [r["profile_id"] for r in recommended if r["role"] == "staff"]

        recommended_alumni = AlumniProfile.objects.filter(id__in=recommended)

        recommended_students = StudentProfile.objects.none()
        recommended_staffs = StaffProfile.objects.none()

        recommended_alumni = AlumniProfile.objects.filter(id__in=recommended_alumni)
        recommended_students = StudentProfile.objects.filter(id__in=recommended_students)
        recommended_staffs = StaffProfile.objects.filter(id__in=recommended_staffs)

    not_count=notification_count
    return render(request, "alumni/newdash.html", {
        "user": user,
        "profile": profile,
        "posts": posts,
        "role":role,
        "suggestions": suggestions,
        "n_count":not_count,
        "recommended_alumni":recommended_alumni,
        "recommended_staffs":recommended_staffs,
        "recommended_students":recommended_students,
        "profile_exists": profile_exists,
    })


import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def recommend_alumni(alumni_queryset, user_id, top_n=5):
    """
    alumni_queryset : Django queryset of AlumniProfile
    user_id          : Logged-in alumni profile ID
    top_n            : Number of recommendations
    """

    # Convert Django queryset to DataFrame
    df = pd.DataFrame(list(alumni_queryset.values()))

    if df.empty or user_id not in df["id"].values:
        return []

    # Combine important profile fields into single text
    df["combined_text"] = (
        df["degree"].fillna("") + " " +
        df["branch"].fillna("") + " " +
        df["skills"].fillna("") + " " +
        df["current_company"].fillna("") + " " +
        df["current_designation"].fillna("") + " " +
        df["location"].fillna("") + " " +
        df["bio"].fillna("")
    )

    # Vectorization (AI step)
    tfidf = TfidfVectorizer(stop_words="english")
    vectors = tfidf.fit_transform(df["combined_text"])

    # Similarity calculation
    similarity_matrix = cosine_similarity(vectors)

    # Get index of current user
    user_index = df[df["id"] == user_id].index[0]

    # Similarity scores
    scores = list(enumerate(similarity_matrix[user_index]))

    # Sort by similarity (high → low)
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    # Get top recommendations (excluding self)
    recommended_ids = []
    for i, score in scores[1: top_n + 1]:
        recommended_ids.append(df.iloc[i]["id"])
    print("********************",recommended_ids)
    return recommended_ids



# def build_profile_text(profile, role):
#     if role == "alumni":
#         return " ".join(filter(None, [
#             profile.degree,
#             profile.branch,
#             profile.skills,
#             profile.current_company,
#             profile.current_designation,
#             profile.location,
#             profile.bio,
#         ]))
#
#     if role == "student":
#         return " ".join(filter(None, [
#             profile.degree,
#             profile.branch,
#             profile.interests,
#             profile.bio,
#         ]))
#
#     if role == "staff":
#         return " ".join(filter(None, [
#             profile.department,
#             profile.subject,
#             profile.achievements,
#             profile.bio,
#         ]))
# import pandas as pd
#
# def get_all_profiles_dataframe():
#     rows = []
#
#     for a in AlumniProfile.objects.select_related("user"):
#         rows.append({
#             "profile_id": a.id,
#             "user_id": a.user.id,
#             "role": "alumni",
#             "text": build_profile_text(a, "alumni"),
#         })
#
#     for s in StudentProfile.objects.select_related("user"):
#         rows.append({
#             "profile_id": s.id,
#             "user_id": s.user.id,
#             "role": "student",
#             "text": build_profile_text(s, "student"),
#         })
#
#     for st in StaffProfile.objects.select_related("user"):
#         rows.append({
#             "profile_id": st.id,
#             "user_id": st.user.id,
#             "role": "staff",
#             "text": build_profile_text(st, "staff"),
#         })
#
#     return pd.DataFrame(rows)


