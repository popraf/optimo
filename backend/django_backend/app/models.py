from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False, blank=False)
    author = models.CharField(max_length=255, null=False, blank=False)
    isbn = models.CharField(max_length=13, null=False, blank=False)
    count_in_library = models.PositiveIntegerField(default=1, null=False, blank=False)
    library = models.CharField(default='Main Library', max_length=255, null=False, blank=False)

    def __str__(self):
        return self.title

    class Meta:
        # Prevents multiple reservations of the same book by the same user.
        unique_together = ('isbn', 'library')


class Reservation(models.Model):
    reservation_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reserved_at = models.DateTimeField(auto_now_add=True)
    reserved_until = models.DateTimeField(null=False, blank=False)
    reservation_status = models.BooleanField(default=True, null=False, blank=False)
    reservation_library = models.CharField(default='Main Library',
                                           max_length=255,
                                           null=False,
                                           blank=False)
    is_external = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return f"{self.user.username} reserved {self.book.title}"

    class Meta:
        # Prevents multiple reservations of the same book by the same user.
        unique_together = ('user', 'book', 'reservation_status')
