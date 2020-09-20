# Generated by Django 3.1.1 on 2020-09-20 00:08

import django.db.models.deletion
from django.db import migrations, models

import reactivated.constraints
import reactivated.fields
import sample.server.apps.samples.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Composer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="ComposerCountry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("was_born", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Continent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "hemisphere",
                    reactivated.fields.EnumField(
                        default=sample.server.apps.samples.models.Continent.Hemisphere[
                            "SOUTHERN"
                        ],
                        enum=sample.server.apps.samples.models.Continent.Hemisphere,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Opera",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "style",
                    reactivated.fields.EnumField(
                        default=sample.server.apps.samples.models.Opera.Style["GRAND"],
                        enum=sample.server.apps.samples.models.Opera.Style,
                    ),
                ),
                ("has_piano_transcription", models.BooleanField(default=False)),
                (
                    "composer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operas",
                        to="samples.composer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Country",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "continent",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="countries",
                        to="samples.continent",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="continent",
            constraint=reactivated.constraints.EnumConstraint(
                field_name="hemisphere",
                members=["SOUTHERN", "NORTHERN"],
                name="samples_continent_hemisphere_enum",
            ),
        ),
        migrations.AddField(
            model_name="composercountry",
            name="composer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="composer_countries",
                to="samples.composer",
            ),
        ),
        migrations.AddField(
            model_name="composercountry",
            name="country",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="composer_countries",
                to="samples.country",
            ),
        ),
        migrations.AddField(
            model_name="composer",
            name="countries",
            field=models.ManyToManyField(
                related_name="composers",
                through="samples.ComposerCountry",
                to="samples.Country",
            ),
        ),
        migrations.AddConstraint(
            model_name="opera",
            constraint=reactivated.constraints.EnumConstraint(
                field_name="style",
                members=["VERISMO", "BUFFA", "GRAND"],
                name="samples_opera_style_enum",
            ),
        ),
    ]
