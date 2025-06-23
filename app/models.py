from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import random
from django.core.exceptions import ValidationError
from PIL import Image

# Create your models here.

class CustomUser(AbstractUser):
    """
    Custom user model that extends AbstractUser.
    """
    USER_TYPES = (
        ('student', 'Student'),
        ('admin', 'Admin'),
    )
    
    is_active = models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.")
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')

    avatar_choices = [
        ('001-superhero.png', 'Hero 1'),
        ('002-superhero-1.png', 'Hero 2'),
        ('003-superhero-2.png', 'Hero 3'),
        ('004-superhero-3.png', 'Hero 4'),
        ('005-superhero-4.png', 'Hero 5'),
        ('006-superhero-5.png', 'Hero 6'),
        ('007-achilles.png', 'Hero 7'),
        ('008-superhero-6.png', 'Hero 8'),
        ('009-superhero-7.png', 'Hero 9'),
        ('010-superhero-8.png', 'Hero 10'),
        ('011-superhero-9.png', 'Hero 11'),
        ('012-superhero-10.png', 'Hero 12'),
        ('013-superhero-11.png', 'Hero 13'),
        ('014-superhero-12.png', 'Hero 14'),
        ('015-batman.png', 'Hero 15'),
    ]

    avatar = models.CharField(max_length=100, choices=[(choice[0], choice[1]) for choice in avatar_choices], blank=True)
    custom_avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar = random.choice([choice[0] for choice in self.avatar_choices])
        super().save(*args, **kwargs)

class SDG(models.Model):
    code = models.CharField(max_length=5, unique=True, blank=True, help_text="e.g. SDG1, SDG2, etc.") 
    name = models.CharField(max_length=255, blank=True, help_text="e.g. No Poverty, Zero Hunger, etc.")         

    def __str__(self):
        return f"{self.code}: {self.name}"

class Theme(models.Model):
    name = models.CharField(max_length=100)  
    description = models.TextField()          
    slug = models.SlugField(unique=True)     
    sdg = models.ManyToManyField(SDG, blank=True)
    color = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Action(models.Model):
    theme = models.ForeignKey('Theme', related_name='actions', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='actions/') 

    def __str__(self):
        return f"{self.name} ({self.theme.name})"
    
class Challenge(models.Model):
    image = models.ImageField(upload_to='challenges/')  # For the background image
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    sdg = models.ManyToManyField(SDG, blank=True)
    points = models.IntegerField()  
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Admin who created the challenge
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    @property
    def days_left(self):
        now = timezone.now().date()
        if self.end_date.date() >= now:
            return (self.end_date.date() - now).days
        return 0 
    
def submission_upload_path(instance, filename):
    """
    Creates a dynamic file path for uploaded submission images.
    """
    if instance.challenge:
        return f"submissions/challenge_{instance.challenge.id}/{instance.user.username}_{filename}"
    else:
        return f"submissions/theme_{instance.theme}/{instance.user.username}_{filename}"

class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')  
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, null=True, blank=True)  
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to=submission_upload_path) 
    title = models.CharField(max_length=255)
    caption = models.TextField()
    points = models.PositiveIntegerField(default=0)
    prediction_label = models.CharField(max_length=100, blank=True, null=True)
    prediction_confidence = models.FloatField(blank=True, null=True)
    prediction_theme_confidence = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Title: Max 5 words
        title_words = self.title.strip().split()
        if len(title_words) > 5:
            raise ValidationError({'title': 'Title must not exceed 5 words.'})

        # Caption: Max 30 words
        caption_words = self.caption.strip().split()
        if len(caption_words) > 30:
            raise ValidationError({'caption': 'Caption must not exceed 30 words.'})

    def save(self, *args, **kwargs):
        if self.challenge:
            self.points = self.challenge.points
        elif self.theme:
            self.points = 50  # Fixed pts for theme-based submission

        super().save(*args, **kwargs)

        # Crop the image to square after saving
        if self.image:
            img_path = self.image.path
            img = Image.open(img_path)

            if img.width != img.height:
                # Center-crop to square
                min_side = min(img.width, img.height)
                left = (img.width - min_side) / 2
                top = (img.height - min_side) / 2
                right = (img.width + min_side) / 2
                bottom = (img.height + min_side) / 2

                img_cropped = img.crop((left, top, right, bottom))
                img_cropped.save(img_path)  # Overwrite the original image
        
    def __str__(self):
        if self.challenge:
            return f"{self.user.username}'s submission for {self.challenge.title}"
        return f"{self.user.username}'s theme-based submission on {self.theme}"
    
