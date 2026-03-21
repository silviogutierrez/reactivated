import enum

import reactivated.constraints
import reactivated.fields
from django.db import migrations


class Status(enum.Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    CLOSED = "Closed"


class Migration(migrations.Migration):

    dependencies = [
        ("example", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="status",
            field=reactivated.fields.EnumField(
                default=Status.DRAFT,
                enum=Status,
            ),
        ),
    ]
