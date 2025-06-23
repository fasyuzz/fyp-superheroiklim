from django.urls import path, include, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgotPassword, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.resetPassword, name='reset_password'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/challenge/<int:challenge_id>/', views.challenge_detail, name='challenge_detail'),
    path('log-action/challenge/<int:challenge_id>/', views.log_action, name='log_action_challenge'),
    path('log-action/theme/<slug:slug>/', views.log_action, name='log_action_theme'),
    path('student/gallery/', views.gallery_view, name='gallery'),
    path('student/leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('student/profile/', views.profile_view, name='profile'),
    path('change-avatar/', views.change_avatar, name='change_avatar'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('challenge/<int:challenge_id>/', views.view_challenge, name='view_challenge'),
    path('challenge/create/', views.create_challenge, name='create_challenge'),
    path('challenge/', views.admin_challenge, name='admin_challenge'),
    path('theme/', views.admin_theme, name='admin_theme'),
    path('gallery/', views.admin_gallery, name='admin_gallery'),
    path('leaderboard/', views.admin_leaderboard, name='admin_leaderboard'),
    path('profile/', views.admin_profile, name='admin_profile'),
    path('challenge/<int:challenge_id>/edit/', views.edit_challenge, name='edit_challenge'),
    path('challenge/<int:challenge_id>/delete/', views.delete_challenge, name='delete_challenge'),
] 

# Add static URL configurations for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', views.serve_media),
    ]
