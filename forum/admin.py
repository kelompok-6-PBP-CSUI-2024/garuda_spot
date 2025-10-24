from django.contrib import admin
from .models import Category, Post, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_name', 'category', 'status', 'created_at', 'like_count')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'body', 'author_name')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-created_at',)
    autocomplete_fields = ('category',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'post', 'created_at')
    search_fields = ('author_name', 'body')
    list_filter = ('created_at',)
