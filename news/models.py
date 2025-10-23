import uuid
from django.db import models

class News(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    category = models.CharField(max_length=100)
    publish_date = models.CharField(max_length=100, blank=True)
    content = models.TextField()

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.title
