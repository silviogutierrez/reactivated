from django.db import models


class Question(models.Model):
    question_text = models.CharField(max_length=200, verbose_name="question")
    pub_date = models.DateTimeField("date published")


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    choice_text = models.CharField(max_length=200, verbose_name="choice")
    votes = models.IntegerField(default=0)
