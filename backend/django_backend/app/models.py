from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False, blank=False)
    author = models.CharField(max_length=255, null=False, blank=False)
    isbn = models.CharField(max_length=13, unique=True, null=False, blank=False)

    def __str__(self):
        return self.title


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    library = models.CharField(default='Main Library', max_length=255, null=False, blank=False)
    reserved_at = models.DateTimeField(auto_now_add=True)
    reserved_until = models.DateTimeField(null=False, blank=False)
    is_reservation_finished = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} reserved {self.book.title}"
