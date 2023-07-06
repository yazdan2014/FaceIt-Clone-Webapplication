from django.db import models
from accounts.models import CustomUser


class News(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    body = models.TextField()


class Comment(models.Model):
    news = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)


# MESSAGING PART


class Message(models.Model):
    sent_from = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='message_sent_from')
    sent_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='message_sent_to')
    message_text = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sent_from} message to {self.sent_from}'
