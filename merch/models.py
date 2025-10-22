from django.db import models

class Merch(models.Model):
    CATEGORY_CHOICES = [
        ('cap', 'Cap'),
        ('hoodie', 'Hoodie'),
        ('jacket', 'Jacket'),
        ('jersey', 'Jersey'),
        ('keychain', 'Keychain'),
        ('scarf', 'Scarf'),
    ]

    name = models.CharField(max_length=255)
    price = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField()
    thumbnail = models.URLField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='update')
    
    def __str__(self):
        return self.name