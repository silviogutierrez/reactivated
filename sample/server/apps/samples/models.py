import enum
from typing import Optional, cast

from django.db import models

from reactivated import computed_foreign_key, computed_relation
from reactivated.fields import EnumField


class Continent(models.Model):
    class Hemisphere(enum.Enum):
        SOUTHERN = "Southern"
        NORTHERN = "Northern"

    name = models.CharField(max_length=100)
    hemisphere = EnumField(enum=Hemisphere, default=Hemisphere.SOUTHERN)


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

    @computed_foreign_key(model=lambda: Opera, null=False)
    def main_opera(self) -> "Opera":
        main = self.operas.all().first()
        assert main is not None
        return main

    @computed_foreign_key(model=lambda: Opera, null=True)
    def favorite_opera(self) -> Optional["Opera"]:
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
    class Style(enum.Enum):
        VERISMO = "Verismo"
        BUFFA = "Opera Buffa"
        GRAND = "Grand Opera"

    name = models.CharField(max_length=100)
    composer = models.ForeignKey(
        "Composer", on_delete=models.CASCADE, related_name="operas"
    )
    style = EnumField(enum=Style, default=Style.GRAND)
    has_piano_transcription = models.BooleanField(default=False)

    objects = cast(OperaManager, OperaManager.from_queryset(OperaQuerySet)())

    def __str__(self) -> str:
        return f"{self.name}: {self.composer.name}"

    def get_birthplace_of_composer(self) -> Optional[str]:
        country = self.composer.countries.filter(
            composer_countries__was_born=True
        ).first()

        if country is not None:
            return country.name

        return None
