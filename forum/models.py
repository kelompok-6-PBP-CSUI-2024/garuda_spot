# forum/models.py
from django.db import models
from django.utils.text import slugify
from django.db.models import F

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    class Meta: ordering = ["name"]
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    def __str__(self): return self.name

class Post(models.Model):
    DRAFT, PUBLISHED = "draft", "published"
    STATUS_CHOICES = [(DRAFT, "Draft"), (PUBLISHED, "Published")]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    author_name = models.CharField(max_length=80, default="Orang")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="posts")
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PUBLISHED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    like_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0) 
    

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)[:220]
        if not self.excerpt: self.excerpt = (self.body or "")[:220]
        super().save(*args, **kwargs)
    def __str__(self): return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author_name = models.CharField(max_length=80, default="Orang")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["created_at"]
    def __str__(self): return f"Comment by {self.author_name}"
