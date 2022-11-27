from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """
    Форма модели поста
    Поля:
    text - текст поста
    group - группа поста
    image - картинка.
    """

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """
    Форма модели комментариев.

    """
    class Meta:
        model = Comment
        fields = ('text',)
