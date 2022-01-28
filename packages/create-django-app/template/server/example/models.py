from django.db import models

from reactivated.serialization import field_descriptor_schema
from reactivated.serialization.registry import register


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


@register(models.BigAutoField)
class BigAutoField:
    @classmethod
    def get_json_schema(Type, instance, definitions):
        return field_descriptor_schema(models.IntegerField(), definitions)
