from django.conf import settings
from django.db import models


# Create your models here.
class CommentModel(models.Model):
    is_active = models.BooleanField(null=True)
    # is_active = models.NullBooleanField()


class CommentModel2(models.Model):
    body = models.CharField(max_length=5000)


class BlogPost(models.Model):
    post = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class CommentModel3(models.Model):
    body = models.TextField()
    date = models.DateField(null=True)


class CommentModel4(models.Model):
    body = models.TextField(null=False, editable=True)


class CommentModel5(models.Model):
    body = models.TextField(null=True)


class BlogPost2(models.Model):
    id = models.UUIDField(primary_key=True, unique=False)
