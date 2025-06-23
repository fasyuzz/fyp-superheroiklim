from django.contrib import admin
from .models import CustomUser, Challenge, Submission, Theme, SDG, Action

# Register your models here.

# admin.site.register(CustomUser)
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff')

class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'start_date', 'end_date', 'created_by')
    list_filter = ('start_date', 'end_date', 'created_by')
    search_fields = ('title',)

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('challenge', 'theme', 'user', 'created_at')
    list_filter = ('challenge', 'user', 'created_at')
    search_fields = ('challenge', 'user')

admin.site.register(Challenge, ChallengeAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Theme)
admin.site.register(SDG)
admin.site.register(Action)

