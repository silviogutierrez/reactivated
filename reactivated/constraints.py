# type: ignore
from django.db import models
from django.db.backends.ddl_references import Statement, Table


class EnumConstraint(models.constraints.BaseConstraint):
    def __init__(self, *, members, name, field_name):
        self.members = members
        self.field_name = field_name
        super().__init__(name)

    def constraint_sql(self, model, schema_editor):
        return ""

    def create_sql(self, model, schema_editor):
        columns = self.members

        return Statement(
            """
            DROP TYPE IF EXISTS %(enum_type)s;
            CREATE TYPE %(enum_type)s AS ENUM (%(columns)s);
            ALTER TABLE %(table)s ALTER COLUMN %(field_name)s TYPE %(enum_type)s USING %(field_name)s::%(enum_type)s;
            """,
            table=Table(model._meta.db_table, schema_editor.quote_name),
            field_name=schema_editor.quote_name(self.field_name),
            columns=", ".join([f"'{column}'" for column in columns]),
            enum_type=schema_editor.quote_name(f"{self.field_name}_enum"),
        )

    def remove_sql(self, model, schema_editor):
        return Statement(
            "ALTER TABLE %(table)s ALTER COLUMN %(field_name)s TYPE varchar(63); DROP TYPE %(enum_type)s;",
            table=Table(model._meta.db_table, schema_editor.quote_name),
            name=schema_editor.quote_name(self.name),
            enum_type=schema_editor.quote_name(f"{self.field_name}_enum"),
            field_name=schema_editor.quote_name(self.field_name),
        )

    def __repr__(self):
        return "<%s: members='%r' name=%r>" % (
            self.__class__.__name__,
            self.members,
            self.name,
        )

    def __eq__(self, other):
        return (
            isinstance(other, EnumConstraint)
            and self.name == other.name
            and self.members == other.members
        )

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["members"] = self.members
        kwargs["field_name"] = self.field_name
        return path, args, kwargs
