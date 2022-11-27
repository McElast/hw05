from django.core.paginator import Paginator
from django.core.cache import cache

from .constans import POST_LIMIT


def paginat(request, posts):
    cache.set("posts", posts, 20)
    paginator = Paginator(posts, POST_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
