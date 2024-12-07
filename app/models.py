from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from uuid import uuid4
import os

class User(AbstractUser):
    #user_id = models.UUIDField(default=uuid4, editable=False, unique=True)
    is_premium = models.BooleanField(default=False)
    btc_address = models.CharField(max_length=255, blank=True, null=True)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_banned = models.BooleanField(default=False)

def video_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_name = f"{uuid4().hex}.{ext}"
    return os.path.join('videos', unique_name)

class Video(models.Model):
    OWNER_TYPE = (
        ('free', 'Free'),
        ('premium', 'Premium'),
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    video_file = models.FileField(upload_to=video_upload_path, validators=[FileExtensionValidator(['mp4','webm'])])
    # Premium videolar için 10sn'lik bir önizleme klibi
    video_preview_file = models.FileField(upload_to=video_upload_path, blank=True, null=True, validators=[FileExtensionValidator(['mp4','webm'])])
    video_type = models.CharField(max_length=10, choices=OWNER_TYPE, default='free')
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    upload_date = models.DateTimeField(auto_now_add=True)
    size_in_bytes = models.BigIntegerField(default=0)

class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class WithdrawRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    btc_address = models.CharField(max_length=255)
    requested_at = models.DateTimeField(auto_now_add=True)
    txid = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)

class VideoLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'video')

class VideoView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'video')
