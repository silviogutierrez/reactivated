from typing import Any, List, Optional, Type

from django.db import models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.ddl_references import Statement, Table
from django.db.models.base import Model


class EnumConstraint(models.constraints.BaseConstraint):
    def __init__(self, *, members: List[str], name: str, field_name: str) -> None:
        self.members = members
        self.field_name = field_name

        # Other libraries, like django extensions, depend on this instance variable.
        self.fields: List[str] = []

        super().__init__(name)

    def constraint_sql(
        self,
        model: Optional[Type[Model]],
        schema_editor: Optional[BaseDatabaseSchemaEditor],
    ) -> str:
        """ We leave this blank as the migration code tries to inject
        constraint code inline with the field, which doesn't work for custom
        types in PostgreSQL.
        """
        return ""

    def create_sql(self, model: Optional[Type[Model]], schema_editor: Optional[BaseDatabaseSchemaEditor]) -> Statement:  # type: ignore[override]
        columns = self.members
        assert model is not None
        assert schema_editor is not None

        return Statement(
            """
            DROP TYPE IF EXISTS %(enum_type)s;
            CREATE TYPE %(enum_type)s AS ENUM (%(columns)s);
            ALTER TABLE %(table)s ALTER COLUMN %(field_name)s TYPE %(enum_type)s USING %(field_name)s::%(enum_type)s;
            """,
            table=Table(model._meta.db_table, schema_editor.quote_name),
            field_name=schema_editor.quote_name(self.field_name),
            enum_type=schema_editor.quote_name(self.name),
            columns=", ".join([f"'{column}'" for column in columns]),
        )

    def remove_sql(self, model: Optional[Type[Model]], schema_editor: Optional[BaseDatabaseSchemaEditor]) -> Statement:  # type: ignore[override]
        assert model is not None
        assert schema_editor is not None

        return Statement(
            "ALTER TABLE %(table)s ALTER COLUMN %(field_name)s TYPE varchar(63); DROP TYPE %(enum_type)s;",
            table=Table(model._meta.db_table, schema_editor.quote_name),
            field_name=schema_editor.quote_name(self.field_name),
            enum_type=schema_editor.quote_name(self.name),
        )

    def __repr__(self) -> str:
        return "<%s: members='%r' name=%r>" % (
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
