from django.db import models


class People(models.Model):
    name = models.CharField(max_length=50)
    money = models.IntegerField(default=0)


