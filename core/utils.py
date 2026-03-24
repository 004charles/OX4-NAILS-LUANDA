from django.conf import settings
from .models import Notification

def send_notification(appointment, notification_type, message_text):
    """
    Utility to send notifications and log them in the database.
    In a real scenario, this would call external APIs (Twilio, SendGrid, etc.)
    """
    # 1. Log the notification in DB
    notification = Notification.objects.create(
        appointment=appointment,
        notification_type=notification_type,
        message=message_text,
        status='sent' # In real life, this would be 'pending' until API confirms
    )
    
    # 2. Simulate sending (Print to console or use Django Email)
    print(f"--- NOTIFICATION SENT [{notification_type.upper()}] to {appointment.client.phone or appointment.client.email} ---")
    print(f"Message: {message_text}")
    print("----------------------------------------------------------------")
    
    # Optional: If email, use Django's send_mail
    if notification_type == 'email' and appointment.client.email:
        from django.core.mail import send_mail
        try:
            send_mail(
                'Atualização de Agendamento - OX4 Nails',
                message_text,
                settings.DEFAULT_FROM_EMAIL,
                [appointment.client.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            notification.status = 'failed'
            notification.save()

    return notification

def log_activity(user, action, details="", request=None):
    """Logs a user action for auditing purposes."""
    from .models import ActivityLog
    
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
            
    ActivityLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        details=details,
        ip_address=ip
    )
    print(f"--- ACTIVITY LOGGED: {action} by {user} ---")
