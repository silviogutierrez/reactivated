from typing import Any

from django.db import models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.ddl_references import Statement, Table
from django.db.models.base import Model
from django.db.utils import DEFAULT_DB_ALIAS


class EnumConstraint(models.constraints.BaseConstraint):
    def __init__(self, *, members: list[str], name: str, field_name: str) -> None:
        self.members = members
        self.field_name = field_name

        # Other libraries, like django extensions, depend on this instance variable.
        self.fields: list[str] = []

        super().__init__(name=name)

    def constraint_sql(
        self,
        model: type[Model] | None,
        schema_editor: BaseDatabaseSchemaEditor | None,
    ) -> str:
        """We leave this blank as the migration code tries to inject
        constraint code inline with the field, which doesn't work for custom
        types in PostgreSQL.
        """
        return ""

    def create_sql(self, model: type[Model] | None, schema_editor: BaseDatabaseSchemaEditor | None) -> Statement:  # type: ignore[override]
        columns = self.members
        assert model is not None
        assert schema_editor is not None

        # https://github.com/django/django/commit/41d8ef18ac2d983bea5ef919615687308ffe41c1
        # This introduced some sort of double create statement appearing when
        # you have params or things like GeneratedField.  So before dropping the
        # enum, we need to alter the column to varchar to be safe. Otherwise we
        # won't be able to drop.
        return Statement(
            """
            ALTER TABLE %(table)s ALTER COLUMN %(field_name)s TYPE varchar(63);
            DROP TYPE IF EXISTS %(enum_type)s;
            CREATE TYPE %(enum_type)s AS ENUM (%(columns)s);
            ALTER TABLE %(table)s ALTER COLUMN %(field_name)s TYPE %(enum_type)s USING %(field_name)s::%(enum_type)s;
            """,
            table=Table(model._meta.db_table, schema_editor.quote_name),
            field_name=schema_editor.quote_name(self.field_name),
            enum_type=schema_editor.quote_name(self.name),
            columns=", ".join([f"'{column}'" for column in columns]),
        )

    def remove_sql(self, model: type[Model] | None, schema_editor: BaseDatabaseSchemaEditor | None) -> Statement:  # type: ignore[override]
        assert model is not None
        assert schema_editor is not None

        return Statement(
            "ALTER TABLE %(table)s ALTER COLUMN %(field_name)s TYPE varchar(63); DROP TYPE %(enum_type)s;",
            table=Table(model._meta.db_table, schema_editor.quote_name),
            field_name=schema_editor.quote_name(self.field_name),
            enum_type=schema_editor.quote_name(self.name),
        )

    def __repr__(self) -> str:
        return "<{}: members='{!r}' name={!r}>".format(
            self.__class__.__name__,
            self.members,
            self.name,
        )

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, EnumConstraint)
            and self.name == other.name
            and self.members == other.members
        )

    def deconstruct(self) -> Any:
        path, args, kwargs = super().deconstruct()
        kwargs["members"] = self.members
        kwargs["field_name"] = self.field_name
        return path, args, kwargs

    def validate(
        self,
        model: type[models.Model],
        instance: models.Model,
        exclude: list[str] | None = None,
        using: Any = DEFAULT_DB_ALIAS,
    ) -> None:
        pass
