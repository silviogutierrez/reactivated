import enum
import os
from typing import Optional, cast

from django.db import models

from reactivated import computed_relation
from reactivated.fields import EnumField

models.QuerySet.__class_getitem__ = classmethod(  # type: ignore[assignment]
    lambda cls, key: cls
)
models.Manager.__class_getitem__ = classmethod(  # type: ignore[assignment]
    lambda cls, key: cls
)


class Continent(models.Model):
    class Hemisphere(enum.Enum):
        SOUTHERN = "Southern"
        NORTHERN = "Northern"

    name = models.CharField(max_length=100)
    hemisphere = EnumField(enum=Hemisphere, default=Hemisphere.SOUTHERN)
    # hemisphere2 = EnumField(enum=Hemisphere, default=Hemisphere.SOUTHERN)
    # hemisphere3 = EnumField(enum=Hemisphere, default=Hemisphere.SOUTHERN)
    # hemisphere4 = EnumField(enum=Hemisphere, default=Hemisphere.SOUTHERN)


if os.environ.get("STAGE") == "four":
    class Thing(enum.Enum):
        ONE = "One"
        TWO = "Two"
        THREE = "Three"
else:
    class Thing(enum.Enum):
        ONE = "One"
        TWO = "Two"


if os.environ.get("STAGE") in ["two", "three", "four"] and os.environ.get("STAGE") != "five":

    class Two(models.Model):
        hemisphere = EnumField(enum=Thing, default=Thing.ONE)

        if os.environ.get("STAGE") == "three":
            hemisphere2 = EnumField(enum=Thing, default=Thing.ONE)

        class Meta:
            indexes = [models.Index(fields=["hemisphere"], name="index_test")]


class Country(models.Model):
    name = models.CharField(max_length=100)
    continent = models.ForeignKey(
        Continent, on_delete=models.CASCADE, related_name="countries"
    )

    def __str__(self) -> str:
        return self.name


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

    @computed_relation(model=lambda: Opera)
    def operas_with_piano_transcriptions(self) -> "models.QuerySet[Opera]":
        return self.operas.all()

    @computed_relation(model=lambda: Opera)
    def main_opera(self) -> Optional["Opera"]:
        return self.operas.all().first()

    @property
    def did_live_in_more_than_one_country(self) -> bool:
        return self.countries.count() > 1

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
        "Composer", on_delete=models.CASCADE, related_name="operas"
    )
    has_piano_transcription = models.BooleanField(default=False)

    objects = cast(OperaManager, OperaManager.from_queryset(OperaQuerySet)())

    # objects: DayQuerySet = cast(DayQuerySet, DayQuerySet.as_manager())  # type: ignore[assignment]

    def __str__(self) -> str:
        return f"{self.name}: {self.composer.name}"

    def get_birthplace_of_composer(self) -> Optional[str]:
        country = self.composer.countries.filter(
            composer_countries__was_born=True
        ).first()

        if country is not None:
            return country.name

        return None

