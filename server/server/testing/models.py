from django.db import models

import decimal


class Category(models.Model):
    name: str = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name


class Trinket(models.Model):
    name: str = models.CharField(max_length=200)
    category: Category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price: decimal.Decimal = models.DecimalField(decimal_places=2, max_digits=10)
    type: str = models.CharField(max_length=100, choices=(
        ('cheap', 'Cheap'),
        ('expensive', 'Expensive'),
    ))

    def __str__(self) -> str:
        return self.name
