import os
from django.test import TestCase, override_settings
from unittest.mock import patch
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from app.models import Reservation, Book
from app.tasks import send_notification


class IntegrationTestsEmail(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email=os.getenv('MY_TEST_NOTIFICATION_EMAIL', 'testuser@example.com'), password='password')
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            count_in_library=5
        )
        self.reservation = Reservation.objects.create(
            user=self.user,
            book=self.book,
            reservation_status=True,
            reserved_until=timezone.now() + timedelta(days=4)
        )

    # The one below sends real email
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    @patch('app.tasks.logger')
    def test_send_real_notification(self, mock_logger):
        send_notification(self.user.id, self.reservation.pk)
        mock_logger.info.assert_called_with('Email sent to user testuser')
