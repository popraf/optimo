import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from app.models import Reservation

logger = logging.getLogger(__name__)


@shared_task
def send_notification(user_id, reservation_id):
    """
    Sending emails to users e.g. about upcoming book return deadline
    """
    try:
        user = User.objects.get(id=user_id)
        reservation = Reservation.objects.get(reservation_id=reservation_id)
        subject = 'Library Reservation Reminder'
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        context = {
            'user': user,
            'reservation': reservation,
        }
        try:
            message = render_to_string('email/reminder_email.txt', context)
        except TemplateDoesNotExist as e:
            logger.error('Template email/reminder_email.txt does not exist')
            raise TemplateDoesNotExist(f'Template {str(e)} does not exist')

        send_mail(subject, message, email_from, recipient_list)
        logger.info(f'Email sent to user {user.username}')
    except User.DoesNotExist:
        logger.error(f'User with id {user_id} does not exist')
        raise
    except Reservation.DoesNotExist:
        logger.error(f'Reservation with id {reservation_id} does not exist')
        raise
    except Exception as e:
        logger.error(f'Error sending email to user {user_id}: {str(e)}')
        raise


@shared_task
def check_reservation_deadlines():
    """
    Periodic task to check for reservations that are about to expire and notify users
    """
    now = timezone.now()
    reminder_time = now + timedelta(days=3)
    reservations = Reservation.objects.filter(
        reservation_status=True,
        reserved_until__gte=now,
        reserved_until__lte=reminder_time
    )
    for reservation in reservations:
        user_id = reservation.user.id
        reservation_id = reservation.reservation_id
        send_notification.delay(user_id, reservation_id)
        logger.info(f'Reminder scheduled for user {reservation.user.username} about reservation {reservation_id}')
