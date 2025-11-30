
from django.db import models
from django.conf import settings
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ('income', 'Ingreso'),
        ('expense', 'Gasto'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPE)
    date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.title} - {self.amount}"

class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    month = models.DateField()  # store as first day of month
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('user','category','month')

    def __str__(self):
        return f"{self.user} - {self.category} - {self.month}"

class RecurringIncome(models.Model):
    FREQUENCY_CHOICES = [
        ('monthly','Monthly'),
        ('biweekly','Biweekly'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='monthly')
    next_date = models.DateField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.amount})"
