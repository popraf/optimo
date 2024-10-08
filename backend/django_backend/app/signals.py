from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Book


@receiver([post_save, post_delete], sender=Book)
def invalidate_books_cache(sender, **kwargs):
    cache.delete('books_list')
