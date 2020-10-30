from django import forms
from django.forms import ModelForm
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        labels = {'group': 'Выберите группу',
                  'text': 'Введите текст',
                  'image': 'Загрузите картинку'}
        help_texts = {'group': 'Из уже существующих',
                      'text': 'Любой текст',
                      'image': 'Любой файл'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Добавьте комментарий', }
        help_texts = {'text': 'Любой комментарий', }
