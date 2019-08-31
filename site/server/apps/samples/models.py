from django.db import models


class Composer(models.Model):
    name = models.CharField(max_length=100)


class Opera(models.Model):
    name = models.CharField(max_length=100)
    composer = models.ForeignKey(Composer, on_delete=models.CASCADE)
