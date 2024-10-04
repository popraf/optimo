from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .models import Reservation
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_notification(user_id, reservation_id):
    """
    Sending emails to users e.g. about upcoming book return deadline
    """
    try:
        user = User.objects.get(pk=user_id)
        reservation = Reservation.objects.get(pk=reservation_id)
        subject = 'Library Reservation Reminder'
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        context = {
            'user': user,
            'reservation': reservation,
        }
        message = render_to_string('email/reminder_email.txt', context)
        send_mail(subject, message, email_from, recipient_list)
        logger.info('Email sent to user %s', user.username)
    except User.DoesNotExist:
        logger.error('User with id %s does not exist', user_id)
    except Reservation.DoesNotExist:
        logger.error('Reservation with id %s does not exist', reservation_id)
    except Exception as e:
        logger.exception('Error sending email to user %s: %s', user_id, e)


@shared_task
def check_reservation_deadlines():
    """
    Periodic task to check for reservations that are about to expire and notify users
    """
    now = timezone.now()
    reminder_time = now + timedelta(days=3)  # 3 days before the return deadline
    reservations = Reservation.objects.filter(
        is_reservation_finished=False,
        reserved_until__gte=now,
        reserved_until__lte=reminder_time
    )
    for reservation in reservations:
        user_id = reservation.user.id
        reservation_id = reservation.id
        send_notification.delay(user_id, reservation_id)
        logger.info('Reminder scheduled for user %s about \
                    reservation %s', reservation.user.username, reservation.id)
