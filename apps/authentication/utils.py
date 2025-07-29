import random
from django.core.mail import EmailMessage, EmailMultiAlternatives
from .models import User, OneTimePassword
from django.conf import settings
from django.template.loader import render_to_string


def generateOtp():
    otp = ''
    for i in range(6):
        otp += str(random.randint(1, 9))
    return otp

def send_code_to_user(email):
    subject = 'Verify Your SmartSpace Account'
    otp_code = generateOtp()
    user = User.objects.get(email=email)
    
    # Plain text version (fallback)
    text_body = (
        f"Hi {user.first_name},\n\n"
        f"Thank you for signing up with SmartSpace.\n\n"
        f"Your verification code is: {otp_code}\n\n"
        f"Please enter this code on the verification page to activate your account.\n\n"
        f"Regards,\nSmartSpace Team"
    )
    
    # Save OTP to database
    OneTimePassword.objects.create(user=user, code=otp_code)
    
    # HTML version
    context = {
        'first_name': user.first_name,
        'otp_code': otp_code,
        'subject': subject
    }
    html_body = render_to_string('emails/email_verification.html', context)
    
    # Send email
    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email]
    )
    email_message.attach_alternative(html_body, "text/html")
    email_message.send(fail_silently=True)

def send_normal_email(data):
    # Plain text version (unchanged)
    text_body = data['email_body']
    
    # HTML version
    context = {
        'email_subject': data['email_subject'],
        'email_body': data['email_body'],
        'subject': data['email_subject']
    }
    html_body = render_to_string('emails/general_notification.html', context)
    
    # Send email
    email_message = EmailMultiAlternatives(
        subject=data['email_subject'],
        body=text_body,
        from_email=settings.EMAIL_HOST_USER,
        to=[data['to_email']]
    )
    email_message.attach_alternative(html_body, "text/html")
    email_message.send()

