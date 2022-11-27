from django.contrib import admin

from .models import Post, Group, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Класс PostAdmin будет конфигуратором интерфейса поста.

    list_display отображает:
    номер, текст поста, дату создания, автора и группу
    соответственно.
    list_editable -отображает поиск по группе
    search_fields -отображает поиск по тексту
    list_filter -  -//-  фильтрация по дате
    empty_value_display - -//- если пустая строка.
    """

    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


admin.site.register(Group)
admin.site.register(Comment)
