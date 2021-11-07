from django.db import models

# Create your models here.
class TelegramGroup(models.Model):
    chat_id = models.IntegerField()
    name = models.CharField(max_length=128, default='')
    receive_notification = models.BooleanField(default=False)

class TelegramUser(models.Model):
    class ROLE(models.TextChoices):
        GUEST = 'guest'
        MEMBER = 'member'
        ADMIN = 'admin'

    chat_id = models.IntegerField()
    username = models.CharField(max_length=128, default='')
    role = models.CharField(max_length=8, default=ROLE.GUEST, choices=ROLE.choices)
    receive_notification = models.BooleanField(default=False)
