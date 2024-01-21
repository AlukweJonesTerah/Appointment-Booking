# # tasks.py
# from email.mime.text import MIMEText
# import smtplib
# import os
# from email.utils import formataddr
# from dotenv import load_dotenv  # pip install python-dotenv
# from config import Config
# from celery import shared_task, Celery
# from celery.contrib.abortable import AbortableTask
# from flask_mail import Message, Mail
# import app
# from celery_worker.celery_worker_app import make_celery
# import logging
#
# smtp_username = os.getenv('MAIL_USERNAME')
# smtp_password = os.getenv('MAIL_PASSWORD')
#
# mail = Mail(app)
# celery = make_celery(app)
# celery.set_default()
#
#
# @shared_task(bind=True, base=AbortableTask)
# @celery.task
# def send_email_with_smtplib(to, subject, body):
#     smtp_server = app.config['MAIL_SERVER']
#     smtp_port = app.config['MAIL_PORT']
#     smtp_username = app.config['MAIL_USERNAME']
#     smtp_password = app.config['MAIL_PASSWORD']
#     sender_email = app.config['MAIL_DEFAULT_SENDER']
#
#     msg = MIMEText(body)
#     msg['Subject'] = subject
#     msg['From'] = formataddr((f'DigiWave', f'{sender_email}'))
#     msg['To'] = to
#
#     try:
#         with smtplib.SMTP(smtp_server, smtp_port) as server:
#             server.starttls()
#             server.login(smtp_username, smtp_password)
#             server.sendmail(sender_email, [to], msg.as_string())
#         logging.info(f'Email sent using smtplib to {to}')
#     except smtplib.SMTPAuthenticationError as e:
#         logging.error(f'SMTP Authentication Error: {str(e)}')
#     except Exception as e:
#         logging.error(f'Failed to send email using smtplib to {to}: {str(e)}', exc_info=True)
#
# @shared_task(bind=True, base=AbortableTask)
# @celery.task
# def send_email_with_flask_mail(to, subject, body):
#     try:
#         msg = Message(subject, recipients=[to], body=body)
#         mail.send(msg)
#         app.logger.info(f'Email sent using Flask-Mail to {to}')
#         return True  # Indicate successful email sending
#     except Exception as e:
#         app.logger.error(f'Failed to send email using Flask-Mail to {to}: {str(e)}')
#         return False  # Indicate failed email sending
