from django.db import models

class Merch(models.Model):
    CATEGORY_CHOICES = [
        ('cap', 'Cap'),
        ('hoodie', 'Hoodie'),
        ('jacket', 'Jacket'),
        ('jersey', 'Jersey'),
        ('keychain', 'Keychain'),
        ('scarf', 'Scarf'),
        ('others', 'Others')
    ]

    name = models.CharField(max_length=255)
    vendor = models.CharField(max_length=255, default='')
    price = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField()
    thumbnail = models.URLField(blank=True, default='')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='others')
    link = models.URLField(blank=True, default='')
    
    def __str__(self):
        return self.name