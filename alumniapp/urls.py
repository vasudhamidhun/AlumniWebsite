from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
urlpatterns=[

    #admin
    path("add-comment/<int:post_id>/", add_comment, name="add_comment"),
    path("like/<int:post_id>/", toggle_like, name="toggle_like"),
    path('adminlogin/',adminlogin,name="adminlogin"),
    path("admindash/",admindash,name="admindash"),
    path('',index,name="index"),
    path('addstaff/', add_staff, name='add_staff'),
    path('updatestaff/<int:id>/', update_staff, name='update_staff'),
    path('delete/<int:id>/', delete_staff, name='delete_staff'),
    path('stafflist/', staff_list, name='staff_list'),

    path('addstud/',add_student,name="add_student"),
    path('studentreg/',student_register,name="student_register"),
    path('register/<str:role>',alumni_register,name="alumni_register"),
    path("verify/<str:token>/<str:role>", verify_email, name="verify_email"),
    path('login/student/', login_view, {'role': 'student'}, name='student_login'),
    path('login/alumni/', login_view, {'role': 'alumni'}, name='alumni_login'),
    path('login/staff/', login_view, {'role': 'staff'}, name='staff_login'),

    path('logout/', logout, name='logout'),

    path('dashboard/', dashboard, name='dashboard'),
    path('personal-dash/',user_dashboard,name='user_dashboard'),
    path('create_profile/',create_profile,name='create_profile'),
    path('update_profile/', update_profile, name='update_profile'),

    path('search/', alumni_search, name='alumni_search'),

    path("user/<int:id>", user_profile, name="user_profile"),

    path("follow/<int:user_id>/", follow_user, name="follow_user"),
    path("follow-back/<int:follower_id>/<int:following_id>/", follow_back, name="follow_back"),
# urls.py
    path('unfollow/<int:user_id>/', unfollow, name='unfollow'),

    path("friends/", friends_list, name="friends_list"),


    path("add-event/", add_event, name="add_event"),
    path("event-success/", event_success, name="event_success"),
    path('events/', view_all_events, name='view_all_events'),

    path('gallery/add/',add_gallery, name='add_gallery'),
    path('gallery_list/',gallery_list,name="gallery_list"),

    path('post/add/',add_post, name='add_post'),
    path('like-post/<int:post_id>/', toggle_like, name='toggle_like'),
    path("delete_post/<int:id>",delete_post,name="delete_post"),
    path("bookmark/<int:id>",bookmark,name="bookmark"),
    path("bookmarks/", bookmarked_posts, name="bookmarked_posts"),


    # password reset urls
    path('password_reset/<str:role>', send_reset_page, name='password_reset'),
    path('password_reset_send/<str:role>', send_reset_email, name='password_reset_send'),
    # Step 2 : Confirmation page (optional)
    path('password_reset_done/',
         auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'),
         name='password_reset_done'),
    # Step 3 : User clicks email link → reset password (your custom)
    path("reset-password/<int:uid>/<str:token>/",
         custom_reset_confirm,
         name="custom_reset_confirm"),
    # Step 4 : Final confirmation (optional)
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'),
         name='password_reset_complete'),

    path('fundraising/new/', fundraising_create, name='fundraising_create'),
    path('fundraising/', fundraising_list, name='fundraising_list'),

    path('jobs/following/', jobs_from_following, name='jobs_from_following'),
    path('jobs/new/',job_create, name='job_create'),

    # messages
    path('messages/', messages_dashboard, name='messages_dashboard'),
    path('chat/<int:follower_id>/', chat_view, name='chat'),
    path('notifications/', notifications, name='notifications'),
    path('send/<int:follower_id>/', send_message, name='send_message'),
    path('ajax-search-friends/', ajax_search_friends, name='ajax_search_friends'),

    ]
