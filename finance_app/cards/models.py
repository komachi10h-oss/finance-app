from django.db import models
from django.conf import settings

class Card(models.Model):
    name = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CardTransaction(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateTimeField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.description} - {self.amount}"

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    belvo_link_id = models.CharField(max_length=200, blank=True, null=True)
    # opcional: guardar last_sync_at, institution, etc.
    last_synced = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"profile: {self.user.username}"
