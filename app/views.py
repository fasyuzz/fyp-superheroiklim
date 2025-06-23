from datetime import datetime, timedelta
import random
import json
import os


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.db.models import Sum, Count, Value, Q, Prefetch
from django.db.models.functions import Coalesce, TruncDate
from django.utils.timezone import now
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives, send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.conf import settings
from django.http import FileResponse, Http404

from .forms import StudentSignUpForm, CustomLoginForm, CustomPasswordResetForm, SubmissionForm, ChallengeForm
from .models import Challenge, Theme, Submission, CustomUser, SDG
from .tokens import account_activation_token
from ml.classifier import classify_image

# Create your views here.

User = get_user_model()

# == Home Page View ==
def index(request):
    return render(request, 'index.html')

# == Activation Views ===
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None 

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Account activated successfully. You can now log in.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid or expired.")
        return redirect('signup')
        
def activateEmail(request, user, email):
    mail_subject = 'Activate your user account - Superhero Iklim'
    html_message = render_to_string('activateAccount.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http',
    })

    text_message = strip_tags(html_message)

    email_obj = EmailMultiAlternatives(
        mail_subject, 
        text_message, 
        to=[email]
    )

    email_obj.attach_alternative(html_message, "text/html")

    if email_obj.send():
        messages.success(request, f"An activation email has been sent to {email}. Please check your inbox to activate your account.")
    else:
        messages.error(request, "Failed to send activation email. Please try again later.")

# == Forgot Password Views ===
def forgotPassword(request):
    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "No user is associated with this email address.")
                return redirect('forgot_password')
            
            mail_subject = 'Reset your password - Superhero Iklim'
            html_message = render_to_string('resetPasswordEmail.html', {
                'user': user.email,
                'domain': get_current_site(request).domain,
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http',
            })

            text_message = strip_tags(html_message)

            try:
                email_obj = EmailMultiAlternatives(
                    mail_subject,
                    text_message,
                    to=[user.email]
                )
                email_obj.attach_alternative(html_message, "text/html")
                email_obj.send()
                messages.success(request, f"A password reset link has been sent to {user.email}. Please check your inbox.")
                return redirect("login")
            except Exception as e:
                messages.error(request, f"Failed to send email. Please try again later.")
    else:
        form = CustomPasswordResetForm()
    return render(request, 'forgotPassword.html', {'form': form}) 


def resetPassword(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        messages.error(request, "The reset link is invalid. Please request a new one.")
        return redirect("login")

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Your password for user {user.username} has been reset. You can now log in with new password.")
                return redirect('login')
        else:
            form = SetPasswordForm(user)
        return render(request, "resetPassword.html", {"form": form})
    else:
        messages.error(request, "The reset link is invalid or expired.")
        return redirect("login")

# == Sign Up and Login Views ===
def signup_view(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect('login')
    else:
        form = StudentSignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST or None)
        username = request.POST.get('username')
        password = request.POST.get('password')
        is_admin_checked = request.POST.get('user_type') == 'admin'

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "Username does not exist.")
            return render(request, 'login.html', {'form': form})
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            if is_admin_checked:
                if user.user_type == 'admin':
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, "Wrong credentials. Please login with the right roles.")
            else:
                if user.user_type == 'student':
                    return redirect('student_dashboard')
                else:
                    messages.error(request, "Wrong credentials. Please login with the right roles.")

            return redirect('login')
        else:
            messages.error(request, "Incorrect password.")
            return render(request, 'login.html', {'form': form})

    else:
        form = CustomLoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('index')

# == Access Control ==
def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != 'admin':
            logout(request)
            messages.error(request, "Admin-only page. You have been logged out.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# == Student Views ===
@login_required
def student_dashboard(request):
    user = request.user
    challenges = Challenge.objects.filter(end_date__gte=datetime.now()).order_by('end_date')
    themes = Theme.objects.all()
    return render(request, 'student/dashboard.html', {'challenges': challenges, 'themes': themes, 'user': user})

@login_required
def challenge_detail(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    return render(request, 'student/joinChallenge.html', {'challenge': challenge})

@login_required
def log_action(request, challenge_id=None, slug=None):
    challenge = Challenge.objects.filter(id=challenge_id).first() if challenge_id else None
    theme = Theme.objects.filter(slug=slug).first() if slug else None
    success = False
    submission = None

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.challenge = challenge
            submission.theme = theme
            submission.save()

            label, confidence, theme_confidence = classify_image(submission.image.path, submission.theme.slug if submission.theme else None)
            submission.prediction_label = label
            submission.prediction_confidence = confidence
            submission.prediction_theme_confidence = round(theme_confidence*100)
            submission.save(update_fields=['prediction_label', 'prediction_confidence', 'prediction_theme_confidence'])

            success = True
    else:
        form = SubmissionForm()

    return render(request, 'student/logAction.html', {
        'form': form,
        'challenge': challenge,
        'theme': theme,
        'success': success,
        'submission': submission,
    })

@login_required
def gallery_view(request):
    query = request.GET.get('q', '')
    selected_challenge = request.GET.get('challenge')
    selected_theme = request.GET.get('theme')
    sort = request.GET.get('sort')

    submissions = Submission.objects.all()

    if query:
        submissions = submissions.filter(Q(title__icontains=query) | Q(caption__icontains=query))
    if selected_challenge:
        submissions = submissions.filter(challenge_id=selected_challenge)
    if selected_theme:
        submissions = submissions.filter(theme_id=selected_theme)

    submissions = submissions.order_by('-created_at' if sort != 'oldest' else 'created_at')

    context = {
        'submissions': submissions,
        'query': query,
        'selected_challenge': selected_challenge,
        'selected_theme': selected_theme,
        'challenges': Challenge.objects.all(),
        'themes': Theme.objects.all(),
    }
    return render(request, 'student/gallery.html', context)

@login_required
def leaderboard_view(request):
    leaderboard = CustomUser.objects.filter(user_type='student') \
        .annotate(total_points=Sum('submissions__points')) \
        .filter(total_points__isnull=False) \
        .order_by('-total_points')
    return render(request, 'student/leaderboard.html', {'leaderboard': leaderboard})


@login_required
def profile_view(request):  
    user = request.user

    if not user.avatar:
        user.avatar = random.choice([choice[0] for choice in CustomUser.avatar_choices])
        user.save()
  
    user_profile = CustomUser.objects.annotate(
        total_points=Coalesce(Sum('submissions__points'), Value(0)),
        submission_count=Coalesce(Count('submissions'), Value(0))
    ).prefetch_related(
        Prefetch('submissions', queryset=Submission.objects.order_by('-created_at'))
    ).filter(id=user.id).first()

    ranked_users = CustomUser.objects.annotate(
        total_points=Coalesce(Sum('submissions__points'), Value(0))
    ).filter(total_points__gt=0).order_by('-total_points', 'id')

    user_rank = next(
        (idx for idx, u in enumerate(ranked_users, start=1) if u.id == user.id),
        None
    ) if user_profile.total_points > 0 else None

    return render(request, 'student/profile.html', {
        'user_profile': user_profile,
        'user_rank': user_rank,
        'avatar': CustomUser.avatar_choices
    })

@login_required
def change_avatar(request):
    if request.method == 'POST':
        avatar = request.POST.get('avatar')
        custom_avatar = request.FILES.get('custom_avatar')

        if custom_avatar:
            request.user.custom_avatar = custom_avatar
            request.user.avatar = ''
        elif avatar in dict(request.user.avatar_choices).keys():
            request.user.avatar = avatar
            request.user.custom_avatar.delete(save=False)
            request.user.custom_avatar = None

        request.user.save()
    return redirect('profile')

# == Admin Views ===
@admin_required
def admin_dashboard(request):
    total_submission_count = Submission.objects.all().count()
    total_user_count =User.objects.filter(user_type='student').distinct().count()

    today = now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    daily_data = Submission.objects \
        .filter(created_at__date__gte=last_7_days[0]) \
        .annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(count=Count('id')) \
        .order_by('date')
    
    data_dict = {d['date']: d['count'] for d in daily_data}
    chart_labels = [d.strftime('%d/%m') for d in last_7_days]  
    chart_data = [data_dict.get(d, 0) for d in last_7_days]

    all_themes = Theme.objects.all()
    submission_counts = Submission.objects.values('theme__id').annotate(count=Count('id'))
    count_map = {item['theme__id']: item['count'] for item in submission_counts}
    theme_labels = [theme.slug.capitalize() for theme in all_themes]
    theme_counts = [count_map.get(theme.id, 0) for theme in all_themes]

    tailwind_color_map = {
    'bg-yellow-300': '#fcd34d',
    'bg-lime-300':   '#bef264',
    'bg-green-300':  '#86efac',
    'bg-purple-300': '#d8b4fe',
    'bg-blue-300':   '#93c5fd',
    }
    
    theme_colors = [tailwind_color_map.get(theme.color, '#d1d5db')  for theme in all_themes]

    threshold_date = now() - timedelta(days=7)
    student_users = User.objects.filter(user_type='student')
    active_users = student_users.filter(last_login__gte=threshold_date).count()
    inactive_users = student_users.exclude(last_login__gte=threshold_date).count()

    return render(request, 'admin/dashboard.html', {
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'theme_labels': theme_labels,
        'theme_counts': theme_counts,
        'theme_colors': theme_colors,
        'user_labels': ['Active', 'Inactive'],
        'user_data': [active_users, inactive_users],
        'total_submission_count': total_submission_count,
        'total_user_count': total_user_count,
    })

@admin_required
def view_challenge(request, challenge_id):
    challenge = Challenge.objects.get(id=challenge_id)
    submissions = Submission.objects.filter(challenge=challenge).order_by('-created_at')
    
    total_submissions = submissions.count()
    total_participants = submissions.values('user').distinct().count() 

    return render(request, 'admin/viewChallenge.html', {
        'challenge': challenge,
        'submissions': submissions,
        'total_submissions': total_submissions,
        'total_participants': total_participants,
    })

@admin_required
def create_challenge(request):
    success = False
    sdg = SDG.objects.all()
    if request.method == 'POST':
        form = ChallengeForm(request.POST, request.FILES)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.created_by = request.user
            challenge.save()
            form.save_m2m()
            success = True
    else:
        form = ChallengeForm()
    return render(request, 'admin/createChallenge.html', {'form': form, 'success': success, 'sdg': sdg})

@admin_required
def edit_challenge(request, challenge_id):
    success = False
    challenge = get_object_or_404(Challenge, id=challenge_id)
    sdg = SDG.objects.all()
    selected_sdgs = [sdg.id for sdg in challenge.sdg.all()] 

    if request.method == 'POST':
        form = ChallengeForm(request.POST, request.FILES, instance=challenge)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.created_by = request.user
            challenge.save()
            form.save_m2m()
            success = True
    else:
        form = ChallengeForm(instance=challenge)
    return render(request, 'admin/editChallenge.html', {'form': form, 'success' : success, 'sdg': sdg, 'selected_sdgs': selected_sdgs})

@admin_required
def delete_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id, created_by=request.user)
    if request.method == 'POST':
        challenge.delete()
        return redirect('admin_challenge')  

@admin_required
def admin_challenge(request):
    ongoing_challenges = Challenge.objects.filter(created_by=request.user, end_date__gte=datetime.now()).order_by('end_date')
    past_challenges = Challenge.objects.filter(created_by=request.user, end_date__lt=datetime.now()).order_by('-end_date')
    return render(request, 'admin/challenges.html', {'ongoing_challenges': ongoing_challenges,'past_challenges': past_challenges,})

@admin_required
def admin_theme(request):
    themes = Theme.objects.all()
    for theme in themes:
        theme.submission_count = Submission.objects.filter(theme=theme).count()
        theme.participant_count = Submission.objects.filter(theme=theme).values('user').distinct().count()
        theme.save()
    submissions = Submission.objects.all()
    return render(request, 'admin/themes.html', {
        'themes': themes,
        'submissions': submissions,
    })
    
@admin_required
def admin_gallery(request):
    query = request.GET.get('q', '')
    selected_challenge = request.GET.get('challenge', '')
    selected_theme = request.GET.get('theme', '')
    sort = request.GET.get('sort')
    submissions = Submission.objects.all()

    if query:
        submissions = submissions.filter(Q(title__icontains=query) | Q(caption__icontains=query))
    if selected_challenge:
        submissions = submissions.filter(challenge_id=selected_challenge)
    if selected_theme:
        submissions = submissions.filter(theme_id=selected_theme)

    submissions = submissions.order_by('-created_at' if sort != 'oldest' else 'created_at')

    context = {
        'submissions': submissions,
        'query': query,
        'selected_challenge': selected_challenge,
        'selected_theme': selected_theme,
        'challenges': Challenge.objects.all(),
        'themes': Theme.objects.all(),
    }

    return render(request, 'admin/gallery.html', context)

@admin_required
def admin_leaderboard(request):
    leaderboard = (
        CustomUser.objects.filter(user_type='student')  
        .annotate(total_points=Sum('submissions__points'))
        .filter(total_points__isnull=False)
        .order_by('-total_points')
    )
    return render(request, 'admin/leaderboard.html', {'leaderboard': leaderboard})

@admin_required
def admin_profile(request):  
    user = request.user

    if not user.avatar:
        user.avatar = random.choice([choice[0] for choice in CustomUser.avatar_choices])
        user.save()

    user_profile = CustomUser.objects.filter(id=user.id).first()
    return render(request, 'admin/profile.html', {'user_profile': user_profile, 'avatar':CustomUser.avatar_choices})   

def serve_media(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    else:
        raise Http404("Media file not found")