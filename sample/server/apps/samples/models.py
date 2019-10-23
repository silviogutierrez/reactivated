from typing import cast

from django.db import models

models.QuerySet.__class_getitem__ = classmethod(  # type: ignore[assignment]
    lambda cls, key: cls
)
models.Manager.__class_getitem__ = classmethod(  # type: ignore[assignment]
    lambda cls, key: cls
)


class Continent(models.Model):
    name = models.CharField(max_length=100)
    hemisphere = models.CharField(max_length=20)


class Country(models.Model):
    name = models.CharField(max_length=100)
    continent = models.ForeignKey(
        Continent, on_delete=models.CASCADE, related_name="countries"
    )


class ComposerCountry(models.Model):
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="composer_countries"
    )
    composer = models.ForeignKey(
        "Composer", on_delete=models.CASCADE, related_name="composer_countries"
    )
    was_born = models.BooleanField(default=False)


class ComposerQuerySet(models.QuerySet["Composer"]):
    def autocomplete(self, query: str) -> models.QuerySet["Composer"]:
        return self.filter(name__icontains=query)


class Composer(models.Model):
    name = models.CharField(max_length=100)
    objects: ComposerQuerySet = cast(  # type: ignore[assignment]
        ComposerQuerySet, ComposerQuerySet.as_manager()
    )

    countries = models.ManyToManyField(
        Country, through=ComposerCountry, related_name="composers"
    )

    def __str__(self) -> str:
        return self.name


class OperaManager(models.Manager["Opera"]):
    pass


class OperaQuerySet(models.QuerySet["Opera"]):
    def autocomplete(self, query: str) -> models.QuerySet["Opera"]:
        return self.filter(name__icontains=query)


class Opera(models.Model):
    name = models.CharField(max_length=100)
    composer = models.ForeignKey(
        Composer, on_delete=models.CASCADE, related_name="operas"
    )
    has_piano_transcription = models.BooleanField(default=False)

    # objects = cast(OperaManager, OperaManager.from_queryset(OperaQuerySet)())

    def __str__(self) -> str:
        return f"{self.name}: {self.composer.name}"
