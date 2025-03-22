from django.db import models
from django.conf import settings

class ChatHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    language = models.CharField(max_length=2, choices=[
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('hr', 'Haryanvi')
    ], default='en')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat History'
        verbose_name_plural = 'Chat Histories'

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
