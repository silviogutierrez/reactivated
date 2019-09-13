from typing import cast

from django.db import models


models.QuerySet.__class_getitem__ = classmethod(lambda cls, key: cls)  # type: ignore
models.Manager.__class_getitem__ = classmethod(lambda cls, key: cls)  # type: ignore


class ComposerQuerySet(models.QuerySet["Composer"]):
    def autocomplete(self, query: str) -> models.QuerySet["Composer"]:
        return self.filter(name__icontains=query)


class Composer(models.Model):
    name = models.CharField(max_length=100)

    objects: ComposerQuerySet = cast(ComposerQuerySet, ComposerQuerySet.as_manager())  # type: ignore

    def __str__(self) -> str:
        return self.name


class OperaManager(models.Manager["Opera"]):
    pass


class OperaQuerySet(models.QuerySet["Opera"]):
    def autocomplete(self, query: str) -> models.QuerySet["Opera"]:
        return self.filter(name__icontains=query)


class Opera(models.Model):
    name = models.CharField(max_length=100)
    composer = models.ForeignKey(Composer, on_delete=models.CASCADE)
    has_piano_transcription = models.BooleanField(default=False)

    # objects = cast(OperaManager, OperaManager.from_queryset(OperaQuerySet)())

    def __str__(self) -> str:
        return f"{self.name}: {self.composer.name}"
