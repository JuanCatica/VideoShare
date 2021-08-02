from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfileInfo(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    user_img = models.ImageField(upload_to='user_img',blank=True, null=True)
    def __str__(self):
        return self.user.username