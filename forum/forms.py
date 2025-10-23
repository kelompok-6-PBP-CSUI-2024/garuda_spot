# forum/forms.py
from django import forms
from .models import Post, Comment, Category

class PostFilterForm(forms.Form):
    q = forms.CharField(required=False)
    category = forms.CharField(required=False)

class PostForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    class Meta:
        model = Post
        fields = ["title", "category", "body", "author_name"]

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["author_name", "body"]
