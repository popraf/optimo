import os
from django.test import TestCase, override_settings
from unittest.mock import patch
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from app.models import Reservation, Book
from app.tasks import send_notification, check_reservation_deadlines
from django.template import TemplateDoesNotExist
from celery import current_app


class SendNotificationTest(TestCase):
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

    @patch('app.tasks.send_mail')
    @patch('app.tasks.logger')
    def test_send_notification_success(self, mock_logger, mock_send_mail):
        mock_send_mail.return_value = 1
        send_notification(self.user.id, self.reservation.pk)
        self.assertTrue(mock_send_mail.called)
        self.assertIn(os.getenv('MY_TEST_NOTIFICATION_EMAIL', 'testuser@example.com'), mock_send_mail.call_args[0][3])
        mock_logger.info.assert_called_with('Email sent to user testuser')

    @patch('app.tasks.render_to_string', side_effect=TemplateDoesNotExist('email/reminder_email.txt'))
    @patch('app.tasks.logger')
    def test_send_notification_missing_template(self, mock_logger, mock_render_to_string):
        with self.assertRaises(Exception) as context:
            send_notification(self.user.id, self.reservation.pk)
        self.assertIn(str(context.exception), 'Template email/reminder_email.txt does not exist')
        mock_logger.error.assert_called_with(f'Error sending email to user {self.user.id}: Template email/reminder_email.txt does not exist')

    @patch('app.tasks.send_mail')
    @patch('app.tasks.logger')
    def test_send_notification_email_failure(self, mock_logger, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP error")
        with self.assertRaises(Exception) as context:
            send_notification(self.user.id, self.reservation.pk)
        mock_logger.error.assert_called_with(f'Error sending email to user {self.user.id}: SMTP error')
        self.assertEqual(str(context.exception), 'SMTP error')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    @patch('django.template.loader.render_to_string')
    @patch('app.tasks.send_mail')
    @patch('app.tasks.logger')
    def test_send_notification_using_default_email_settings(self, mock_logger, mock_send_mail, mock_render_to_string):
        # Mock render_to_string to return valid content so that send_mail can proceed
        mock_render_to_string.return_value = 'This is a reminder email'
        mock_send_mail.return_value = 1

        send_notification(self.user.id, self.reservation.pk)
        self.assertTrue(mock_send_mail.called)
        mock_logger.info.assert_called_with('Email sent to user testuser')


class CheckReservationDeadlinesTest(TestCase):
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
            reserved_until=timezone.now() + timedelta(days=2)
        )
        self.reservation_outside = Reservation.objects.create(
            user=self.user,
            book=self.book,
            reservation_status=True,
            reserved_until=timezone.now() + timedelta(days=10)
        )

    @patch('app.tasks.send_notification.delay')
    def test_check_reservation_deadlines(self, mock_send_notification_delay):
        check_reservation_deadlines()
        mock_send_notification_delay.assert_called_once_with(self.user.id, self.reservation.pk)

    @patch('app.tasks.send_notification.delay')
    def test_check_reservation_deadlines_no_reservations(self, mock_send_notification_delay):
        Reservation.objects.all().delete()
        check_reservation_deadlines()
        mock_send_notification_delay.assert_not_called()

    @patch('app.tasks.send_notification.delay')
    def test_check_reservation_deadlines_multiple_reservations(self, mock_send_notification_delay):
        reservation_2 = Reservation.objects.create(
            user=self.user,
            book=self.book,
            reservation_status=True,
            reserved_until=timezone.now() + timedelta(days=2)
        )
        check_reservation_deadlines()
        self.assertEqual(mock_send_notification_delay.call_count, 2)
        mock_send_notification_delay.assert_any_call(self.user.id, self.reservation.pk)
        mock_send_notification_delay.assert_any_call(self.user.id, reservation_2.pk)


class CeleryWorkerTest(TestCase):
    def test_celery_worker_is_running(self):
        inspector = current_app.control.inspect()
        active_workers = inspector.active()
        self.assertIsNotNone(active_workers, "No active Celery workers found.")

    @patch('celery.current_app.control.inspect')
    def test_celery_worker_unavailable(self, mock_inspect):
        mock_inspect.return_value.active.return_value = None
        inspector = current_app.control.inspect()
        active_workers = inspector.active()
        self.assertIsNone(active_workers, "Expected no active Celery workers.")
