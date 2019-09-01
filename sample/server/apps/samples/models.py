from django.db import models


class Composer(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Opera(models.Model):
    name = models.CharField(max_length=100)
    composer = models.ForeignKey(Composer, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.name}: {self.composer.name}"
