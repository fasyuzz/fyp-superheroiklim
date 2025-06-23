from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Submission, Challenge, Theme
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django import forms

input_class = 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500'
input_class_2 = 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-red-800'
input_class_login = 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-800'
theme_class = 'block text-sm font-semibold px-3 py-2 mt-2 rounded-full border-2 w-fit'

User = get_user_model()

class StudentSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="First Name", widget=forms.TextInput(attrs={'class': input_class_login}))
    last_name = forms.CharField(max_length=30, required=True, label="Last Name", widget=forms.TextInput(attrs={'class': input_class_login}))
    password1 = forms.CharField(
        max_length=128,
        required=True,
        label="Password",
        widget=forms.PasswordInput(attrs={'class': input_class_login})
    )
    password2 = forms.CharField(
        max_length=128,
        required=True,
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': input_class_login})
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': input_class_login}),
            'email': forms.EmailInput(attrs={'class': input_class_login}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        if commit:
            user.save()
        return user

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': input_class_login}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': input_class_login}))

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError("The username does not exist. Please sign up first.", code='inactive')

class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': input_class_login}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("No user is associated with this email address.")
        return email
    
class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['image', 'title', 'caption']
        widgets = {
            'image': forms.ClearableFileInput,
            'title': forms.TextInput(attrs={
                'class': input_class,
                'placeholder': 'Enter title',
            }),
            'caption': forms.Textarea(attrs={
                'class': input_class,
                'rows': 5,
                'placeholder': 'Write a caption...',
            }),
        }

class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = ['image', 'title', 'description', 'start_date', 'end_date', 'sdg', 'points']
        widgets = {
            'image': forms.ClearableFileInput,
            'title': forms.TextInput(attrs={
                'class': input_class_2,
                'placeholder': 'Enter title',
            }),
            'description': forms.Textarea(attrs={
                'class': input_class_2,
                'rows': 5,
                'placeholder': 'Write a description...',
            }),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': input_class_2}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': input_class_2}),
            'sdg': forms.CheckboxSelectMultiple(attrs={'class': 'sdg-checkbox'}),
            'points': forms.NumberInput(attrs={'class': input_class_2, 'placeholder': 'Enter points'}),
        }