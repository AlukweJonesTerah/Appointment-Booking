# app.py
# from app_factory import create_app
import logging

import pytz as pytz
from flask import Flask, render_template, url_for, flash, jsonify, request, redirect, session, make_response

# database imports
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from oauthlib.oauth2 import OAuth2Error
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import DateTime

# Login imports
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# session imports
from flask_session import Session
from config import Config
from loggings import configure_logging
from celery_worker.celery_worker_app import make_celery

# form imports
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Regexp, Email, DataRequired
import re
from email_validator import validate_email, EmailNotValidError
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFProtect

# ecryption
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_talisman import Talisman
# from task import send_email_with_flask_mail, send_email_with_smtplib

# Google imports
import datetime as dt
import json
import os.path
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauthlib.oauth2 import OAuth2Error
from google.oauth2 import service_account
from typing import cast


# fast api imports and Mail import
from fastapi import BackgroundTasks
from celery import shared_task, Celery
from celery.contrib.abortable import AbortableTask
from flask_mail import Message, Mail
from celery_worker.celery_worker_app import make_celery
from email.mime.text import MIMEText
import smtplib
import os
from email.utils import formataddr

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
db = SQLAlchemy(app)

# Configure logging
configure_logging(app, config=Config)
# csrf = CSRFProtect(app)
tailsman = Talisman(app)
logging.basicConfig(level=logging.INFO)
# csrf = CSRFProtect(app)

# Initialize Flask extensions

migrate = Migrate(app, db)
Session(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

mail = Mail(app)
celery = make_celery(app)
celery.set_default()


@app.errorhandler(SQLAlchemyError)
def handle_database_error(e):
    # Log error
    app.logger.error(f'Database error: {str(e)}')
    # user-friendly response
    return jsonify({'error': 'A database error occurred'}), 500


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    google_calendar_token = db.Column(db.String(1000))  # store google calendar api token
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def set_google_calendar_token(self, token_json):
        self.google_calendar_token = token_json
        db.session.commit()
        print(f"User ID: {self.id}, Google Calendar Token: {token_json}")

    def get_google_calendar_token(self):
        # return self.google_calendar_token
        return json.loads(self.google_calendar_token) if self.google_calendar_token else None


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))
    event_id = db.Column(db.String(255), unique=True)
    date = db.Column(db.DateTime(timezone=True))
    time = db.Column(db.String(10))
    title = db.Column(db.String(100))
    location = db.Column(db.String(100))
    description = db.Column(db.Text())

    def __init__(self, user_id, date, event_id, time, title, location, description):
        self.user_id = user_id
        self.event_id = event_id
        self.date = date
        self.time = time
        self.title = title
        self.location = location
        self.description = description


# db.init_app(app)
with app.app_context():
    db.create_all()


# form
class RegistrationForm(FlaskForm):
    first_name = StringField(validators=[InputRequired(), Length(max=30),
                                         Regexp('^[a-zA-Z-]+$',
                                                message='First name can only contain letters and hyphens')],
                             render_kw={"placeholder": "Fist Name"})
    last_name = StringField(validators=[InputRequired(), Length(max=30),
                                        Regexp('^[a-zA-Z-]+$',
                                               message='Last name can only contain letters and hyphens')],
                            render_kw={"placeholder": "Last Name"})
    phone_number = StringField(
        validators=[InputRequired(), Regexp('^[0-9]+$', message='Phone number can only contain numbers'),
                    Length(min=10, max=15)],
        render_kw={"placeholder": "Phone Number"})
    email = StringField(validators=[InputRequired(), Email(), Length(max=50)],
                        render_kw={"placeholder": "Email"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=20),
                                       Regexp('^[a-zA-Z0-9_.-]+$',
                                              message="Username can only contain letters. numbers, underscores, dots, "
                                                      "and hyphens")],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20),
                                         Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*()-_+=]).*$',
                                                message="Password must contain at least one lowercase letter, "
                                                        "one uppercase letter, one digit, and one special character")],
                             render_kw={"placeholder": "password"})

    submit = SubmitField('Register')

    def validate_field_without_whitespace(self, field):
        if field.data.strip() != field.data:
            raise ValidationError('Field cannot have leading or trialing whitespaces.')
        try:
            email = validate_email(field.data).email
        except EmailNotValidError as e:
            raise ValidationError(f'Invalid email {e}')

    def validate_first_name(self, first_name):
        if not re.match("^[a-zA-Z-]+$", first_name.data):
            raise ValidationError('First name can only contain letters and hyphens.')
        if '  ' in first_name.data:
            raise ValidationError('First name cannot contain consecutive spaces.')

        if not first_name.data.isalpha():
            raise ValidationError('First name can only contain letters.')

    def validate_last_name(self, last_name):
        if not re.match("^[a-zA-Z-]+$", last_name.data):
            raise ValidationError('Last name can only contain letters and hyphens.')

        if '  ' in last_name.data:
            raise ValidationError('Last name cannot contain consecutive spaces.')

        if not last_name.data.isalpha():
            raise ValidationError('Last name can only contain letters.')

    def validate_phone_number(self, phone_number):
        if not re.match("^[0-9]+$", phone_number.data):
            raise ValidationError('Phone number can only contain numbers.')

            # Check for a valid phone number length (adjust as needed)
        min_length = 10
        max_length = 15
        if not min_length <= len(phone_number.data) <= max_length:
            raise ValidationError(f'Phone number must be between {min_length} and {max_length} digits long.')
        # Check for a valid country code

        # valid_country_codes = ['+1', '+44', '+81', '+254', '+255']  # Add more country codes as needed
        # if not any(phone_number.data.startswith(code) for code in valid_country_codes):
        #     raise ValidationError('Invalid country code.')

        # Ensure the phone number doesn't start with a leading zero
        if phone_number.data.startswith('0'):
            raise ValidationError('Phone number cannot start with a leading zero.')

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError('That email address is already registered. Please use a different one.')
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, email.data):
            raise ValidationError('Invalid email format.')

        allowed_domains = ['example.com', 'gmail.com', 'kabarak.ac.ke']
        if email.data.split('@')[1] not in allowed_domains:
            raise ValidationError('Invalid email domain.')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username is already taken. Please choose a different one.')
        if not username.data[0].isalpha():
            raise ValidationError('Username must start with a letter.')
        if not username.data.isalnum():
            raise ValidationError('Username can only contain letters and numbers.')

    def validate_password(self, password):
        if not any(char.isupper() for char in password.data):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not any(char.islower() for char in password.data):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not any(char.isdigit() for char in password.data):
            raise ValidationError('Password must contain at least one digit.')
        special_characters = "!@#$%^&*()-_+=<>,.?/:;{}[]|"
        if not any(char in special_characters for char in password.data):
            raise ValidationError('Password must contain at least one special character (!@#$%^&*()-_+=<>,.?/:;{}[]|).')
        if self.username.data.lower() in password.data.lower():
            raise ValidationError('Password cannot contain the username.')
        consecutive_char = {''.join(chr(ord(c) + i) for i in range(3)) for c in 'abcdefghijklmnopqrstuvwxyz'} | {
            ''.join(str(i) for i in range(3))}
        if any(consecutive in password.data.lower() for consecutive in consecutive_char):
            raise ValidationError('Password cannot contain consecutive characters (e.g., "abc", "123").')
        if any(password.data.count(char * 2) for char in password.data):
            raise ValidationError('Password cannot contain repeated characters (e.g., "aa", "111").')
        min_length = 8
        if len(password.data) < min_length:
            raise ValidationError(f'Password must be at least {min_length} characters long.')
        max_length = 20
        if len(password.data) > max_length:
            raise ValidationError(f'Password must be at most {max_length} characters long.')



# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     form = RegistrationForm()
#
#     if form.validate_on_submit():
#         hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
#         new_user = User(first_name=form.first_name.data, last_name=form.last_name.data,
#                         phone_number=form.phone_number.data, email=form.email.data, username=form.username.data,
#                         password=hashed_password)
#         db.session.add(new_user)
#         db.session.commit()
#
#         return jsonify({'message': 'Registration successful'}), 200
#
#     # Form is not valid
#     errors = {'errors': {field.name: field.errors for field in form}}
#     return jsonify(errors), 400


@app.route('/setcookies')
def setcookies():
    resp = make_response('Setting the cookies')
    resp.set_cookie('GFG', 'ComputerSciencePortal')
    return resp


@app.route('/getcookie')
def getcookie():
    GFG = request.cookies.get('GFG')
    return 'GFG is a' + GFG


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(first_name=form.first_name.data, last_name=form.last_name.data,
                        phone_number=form.phone_number.data, email=form.email.data, username=form.username.data,
                        password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            try:
                # Obtain the Google Calendar token using your custom function (get_google_auth)
                credentials = get_google_auth()

                if credentials:
                    # Print the obtained token
                    # obtained_token = credentials.to_json()
                    obtained_token = json.dumps(credentials)
                    print(f"Obtained Token during registration: {obtained_token}")
                    flash(f'Success Obtained Token during registration: {obtained_token}', 'success')

                    new_user.set_google_calendar_token(obtained_token)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                logging.error(f'Error saving Google Calendar token: {str(e)}')
                flash(f'Error saving Google Calendar token: {str(e)}', 'danger')

            flash('Account was created successfully', 'success')
            return redirect(url_for('login'))
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f'Error we could not save your details!: {str(e)}', 'danger')
            flash(f'Error we could not save your details!: {str(e)}', 'danger')

    return render_template('register.html', form=form)


# field validation section
@app.route('/validation/<field>', methods=['POST'])
def validation_field(field):
    data = request.get_json()
    value_to_validate = data.get(field, '')

    # Perform validation logic here
    validation_result = validate_field_logic(field, value_to_validate)
    return jsonify({'message': validation_result})


def validate_field_logic(field, value):
    # Perform field-specific validations logic here
    if field == 'first_name':
        min_length, max_length = 2, 50
        if not value:
            return 'First name is required.'
        elif not value.isalpha():
            return 'First name should contain only alphabetic characters'
        elif not (min_length <= len(value) <= max_length):
            return f'First name should be between {min_length} and {max_length} characters'
        elif not re.match("^[a-zA-Z-]+$", value):
            return 'First name can only contain letters and hyphens.'
        elif '  ' in value:
            return 'First name cannot contain consecutive spaces.'
        else:
            return 'First name valid'
    elif field == 'last_name':
        min_length, max_length = 2, 50
        if not value:
            return 'Last name is required.'
        elif not value.isalpha():
            return 'Last name should contain only alphabetic characters'
        elif not (min_length <= len(value) <= max_length):
            return f'Last name should be between {min_length} and {max_length} characters'
        elif not re.match("^[a-zA-Z-]+$", value):
            return 'Last name can only contain letters and hyphens.'
        elif '  ' in value:
            return 'Last name cannot contain consecutive spaces.', 401
        else:
            return 'Last name valid'
    elif field == 'phone_number':
        min_length, max_length = 10, 15
        if not value:
            return 'Phone number is required.'
        elif not re.match("^[0-9]+$", value):
            return 'Phone number can only contain numbers.'
        elif not min_length <= len(value) <= max_length:
            return f'Phone number must be between {min_length} and {max_length} digits long.'
        elif value.startswith('0'):
            return 'Phone number cannot start with a leading zero.'
        else:
            return 'Phone is valid'
    elif field == 'email':
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        allowed_domains = ['example.com', 'gmail.com', 'kabarak.ac.ke']
        if not value:
            return 'Email is required.'
        elif User.query.filter_by(email=value).first():
            return 'That email is already registered.'
        elif not re.match(email_pattern, value):
            return 'Invalid email format.'
        elif value.split('@')[1] not in allowed_domains:
            return 'Invalid email domain.'
        else:
            return 'Email is valid.'
    elif field == 'username':
        if not value:
            return 'Username is required.'
        elif User.query.filter_by(username=value).first():
            return 'Username is already taken.'
        elif not value[0].isalpha():
            return 'Username must start with a letter.'
        elif not value.isalnum():
            return 'Username can only contain letters and numbers.'
        else:
            return 'Username is valid.'
    elif field == 'password':
        special_characters = "!@#$%^&*()-_+=<>,.?/:;{}[]|"
        consecutive_char = {''.join(chr(ord(c) + i) for i in range(3)) for c in 'abcdefghijklmnopqrstuvwxyz'} | {
            ''.join(str(i) for i in range(3))}
        min_length, max_length = 8, 20
        if not value:
            return 'Password is required.'
        elif not any(char.isupper() for char in value):
            return 'Password must contain at least one uppercase letter.'
        elif not any(char.islower() for char in value):
            return 'Password must contain at least one lowercase letter.'
        elif not any(char.isdigit() for char in value):
            return 'Password must contain at least one digit.'
        elif not any(char in special_characters for char in value):
            return 'Password must contain at least one special character (!@#$%^&*()-_+=<>,.?/:;{}[]|).'
        # elif value.lower() in value.lower():
        #     return 'Password cannot contain the username.'
        elif any(consecutive in value.lower() for consecutive in consecutive_char):
            return 'Password cannot contain consecutive characters (e.g., "abc", "123").'
        elif any(value.count(char * 2) for char in value):
            return 'Password cannot contain repeated characters (e.g., "aa", "111").'
        elif len(value) < min_length:
            return f'Password must be at least {min_length} characters long.'
        elif len(value) > max_length:
            return f'Password must be at most {max_length} characters long.'
        else:
            return 'Password valid.'
    else:
        return 'Validation successful.'


@app.route('/login', methods=['GET'])
def login_page():
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/login', methods=['POST'])
def login():
    form = LoginForm(request.form)

    try:
        if request.method == 'POST':
            if form.validate_on_submit() or form.validate():
                user = User.query.filter_by(username=form.username.data).first()

                if user and bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user)
                    # Todo: consider removing session line
                    session['username'] = form.username.data

                    # Check for AJAX requests, return response
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'message': 'Login was successful', 'redirect': url_for('index')})

                    flash(f'Login was successful. Welcome, {current_user.username}!', 'success')

                    app.logger.info(f'Successful login: {current_user.username}')

                    return redirect(url_for('index'))
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'message': 'Invalid username or password'})
                    flash('Invalid username or password. Please try again.', 'danger')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'message': 'Form validation failed'})
        flash('Form validation failed. Please try again.', 'danger')

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'message': 'An error occurred during login.'})
        app.logger.error(f'Error during login: {e}')
        flash('An error occurred during login. Please try again.', 'danger')
    return render_template('login.html', form=form)


def get_user_email(user=None):
    if isinstance(user, int):
        # If the user is provided as an ID, fetch the user actual instance
        user = User.query.get(user)
    email = getattr(user, 'email', None)
    if email:
        return email
    else:
        logging.warning(f"Failed to retrieve email for user: {user}")
    return None


@app.before_request
def before_request():
    if 'user_id' in session:
        session.permanent = True


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    if current_user.is_authenticated:
        current_user.last_activity = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User not authenticated'}), 401


@app.route('/leave-site', methods=['POST'])
def leave_site():
    if current_user.is_authenticated:
        current_user.last_activity = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User not authenticated'}), 401


@app.route('/logout')
@login_required
def logout():
    logout_user()
    if request.is_json:
        return jsonify({'message': 'Logout successful', 'redirect': url_for('login')}), 200
    else:
        flash('You have logged out', 'info')
        return redirect(url_for('login'))


SCOPES = ['https://www.googleapis.com/auth/calendar']


def handle_missing_client_secret():
    try:
        raise FileNotFoundError("Client secret file is missing")
    except FileNotFoundError as e:
        logging.error('Client secret file is missing: %s', e)
        flash("Client secret file is missing. Please check your configuration.", 'danger')
        # Redirect to a page with instructions or display a user-friendly message
        return redirect(url_for('instructions_page'))  # Replace 'instructions_page' with the actual route

# def get_google_auth():
#     creds = None
#     try:
#         if os.path.exists("token.json"):
#             creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 creds.refresh(Request())
#             else:
#                 creds = run_local_server_flow()
#         print(f"Creds: {creds}")
#         print(f"Creds JSON: {creds.to_json()}")
#
#     except FileNotFoundError as file_not_found_error:
#         logging.error("Token file not found: %s", file_not_found_error)
#         flash("Token file not found. Please check your configuration.", 'danger')
#     except google.auth.exceptions.RefreshError as refresh_error:
#         logging.error("Error refreshing credentials: %s", refresh_error)
#         flash("Error refreshing credentials.", 'danger')
#     except Exception as generic_error:
#         logging.error("Error in get_google_auth: %s", generic_error)
#         flash("An unexpected error occurred while fetching Google authentication.")
#
#     return credentials_to_dict(creds) if creds else None

def get_google_auth():
    creds = None
    try:
        if os.path.exists("token.json"):
            # Load credentials directly as a dictionary
            with open("token.json", "r") as token_file:
                creds = json.load(token_file)

        if not creds or not creds.get('client_secret'):
            # If creds is not a valid dictionary, use run_local_server_flow
            creds = run_local_server_flow()

        # If creds is a dictionary, reconstruct Credentials object
        if isinstance(creds, dict):
            creds = Credentials.from_authorized_user_info(creds, SCOPES)

        # Handle the case where creds is None
        if creds is None:
            logging.warning("No valid credentials obtained.")

    except FileNotFoundError as file_not_found_error:
        logging.error("Token file not found: %s", file_not_found_error)
        flash("Token file not found. Please check your configuration.", 'danger')
    except google.auth.exceptions.RefreshError as refresh_error:
        logging.error("Error refreshing credentials: %s", refresh_error)
        flash("Error refreshing credentials.", 'danger')
    except Exception as generic_error:
        logging.error("Error in get_google_auth: %s", generic_error)
        flash("An unexpected error occurred while fetching Google authentication.")

    return credentials_to_dict(creds) if creds else {'client_secret': 'missing'}

# def run_local_server_flow():
#     try:
#         if not os.path.exists("client_secret.json"):
#             raise FileNotFoundError("Client secret file is missing")
#
#         flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
#         creds = flow.run_local_server(port=0)
#
#         if current_user.is_authenticated:
#             current_user.set_google_calendar_token(creds.to_json())
#
#         with open("token.json", "w") as token_file:
#             token_file.write(creds.to_json())
#
#         return creds
#
#     except Exception as e:
#         logging.error('Error in run_local_server_flow: %s', e)
#         raise ValueError("Error during local server flow")

# def run_local_server_flow():
#     try:
#         if not os.path.exists("client_secret.json"):
#             raise FileNotFoundError("Client secret file is missing")
#
#         flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
#         creds = flow.run_local_server(port=0)
#
#         if current_user.is_authenticated:
#             current_user.set_google_calendar_token(credentials_to_dict(creds))
#
#         with open("token.json", "w") as token_file:
#             token_file.write(json.dumps(credentials_to_dict(creds)))
#
#         return creds
#
#     except Exception as e:
#         logging.error('Error in run_local_server_flow: %s', e)
#         raise ValueError("Error during local server flow")

def run_local_server_flow():
    try:
        if not os.path.exists("client_secret.json"):
            raise FileNotFoundError("Client secret file is missing")

        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
        creds = flow.run_local_server(port=0)

        if current_user.is_authenticated:
            current_user.set_google_calendar_token(credentials_to_dict(creds))

        with open("token.json", "w") as token_file:
            # Save the credentials directly as a dictionary
            json.dump(credentials_to_dict(creds), token_file)

        return creds

    except Exception as e:
        logging.error('Error in run_local_server_flow: %s', e)
        raise ValueError("Error during local server flow")

# def credentials_to_dict(credentials):
#     return {
#         'token': credentials.token,
#         'refresh_token': credentials.refresh_token,
#         'token_uri': credentials.token_uri,
#         'client_id': credentials.client_id,
#         'scopes': credentials.scopes,
#     }

def credentials_to_dict(credentials):
    return credentials.to_json() if credentials else None

@app.route('/oauth2callback')
def oauth2callback():
    try:
        flow_creds = get_google_auth()
        state = session.get('oauth_state')

        if not state:
            return render_template('error.html', message='Invalid OAuth state'), 400

        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar'],
            state=state
        )

        try:
            flow.fetch_token(authorization_response=request.url)
            logging.info('OAuth callback successful. Fetching Google Calendar API tokens.')
        except OAuth2Error as oauth_error:
            logging.error(f'OAuth error: {str(oauth_error)}')
            return render_template('error.html', message='OAuth error. Please try again.'), 500
        except Exception as e:
            logging.error(f'Error fetching OAuth tokens: {str(e)}')
            return render_template('error.html', message='Error fetching OAuth tokens'), 500

        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)

        if not flow_creds or not flow_creds.valid:
            handle_token_refresh(flow_creds)

        if not session['credentials']:
            logging.error('No credentials found in the session.')
            return render_template('error.html', message='No credentials found in the session.'), 500

        service = build('calendar', 'v3', credentials=session['credentials'])

    except Exception as e:
        logging.error(f'Error in oauth2callback: {str(e)}')
        return render_template('error.html', message='An error occurred during OAuth callback'), 500

    return redirect(url_for('index'))

def handle_token_refresh(flow_creds):
    if flow_creds and hasattr(flow_creds, 'expired') and flow_creds.expired and hasattr(flow_creds, 'refresh_token') and flow_creds.refresh_token:
        try:
            flow_creds.refresh(Request())
            logging.info('Token refresh successful')
            current_user.set_google_calendar_token(flow_creds.to_json())
            db.session.commit()
        except Exception as e:
            logging.error(f'Token refresh error: {str(e)}')
            return render_template('error.html', message='Error refreshing OAuth tokens'), 500

        with open("token.json", "w") as token:
            token.write(flow_creds.to_json())

# def handle_token_refresh(flow_creds):
#     if flow_creds and hasattr(flow_creds, 'expired') and flow_creds.expired and hasattr(flow_creds, 'refresh_token') and flow_creds.refresh_token:
#         try:
#             flow_creds.refresh(Request())
#             logging.info('Token refresh successful')
#             current_user.set_google_calendar_token(credentials_to_dict(flow_creds))
#             db.session.commit()
#         except Exception as e:
#             logging.error(f'Token refresh error: {str(e)}')
#             return render_template('error.html', message='Error refreshing OAuth tokens'), 500
#
#         with open("token.json", "w") as token:
#             token.write(json.dumps(credentials_to_dict(flow_creds)))

import time
from googleapiclient.errors import HttpError

def exponential_backoff(max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            # Replace the following line with your actual Google Calendar API request
            response = get_google_calendar_service()
            return response
        except HttpError as error:
            if error.resp.status == 403:
                # Exponential backoff: wait 2^retries seconds
                wait_time = 2**retries
                time.sleep(wait_time)
                retries += 1
            else:
                raise
    raise Exception("Max retries reached, still receiving 403 error.")



# def get_google_calendar_service():
#     try:
#         credentials = get_google_auth()
#         service = build('calendar', 'v3', credentials=credentials)
#
#     except google.auth.exceptions.RefreshError as refresh_error:
#         logging.error(f'Token refresh error: {str(refresh_error)}')
#         raise ValueError('Error refreshing Google Calendar API token')
#
#     except google.auth.exceptions.AuthError as auth_error:
#         logging.error(f'Authentication error: {str(auth_error)}')
#         return render_template('error.html', message='Authentication error. Please re-authenticate.'), 401
#
#     except google.auth.exceptions.TransportError as transport_error:
#         logging.error(f'Transport error: {str(transport_error)}')
#         raise ValueError('Error obtaining Google Calendar API service')
#
#     except HttpError as http_error:
#         if http_error.resp.status == 401:
#             return render_template('login.html', message='Authentication failed. Please log in again.'), 401
#         else:
#             logging.error(f'Google Calendar API Error: {http_error}')
#             raise ValueError(f'Google Calendar API Error: {http_error}')
#
#     return service

# def get_google_calendar_service():
#     # Define the maximum number of retries
#     max_retries = 5
#     retry_count = 0
#
#     while retry_count < max_retries:
#         try:
#             credentials = get_google_auth()
#
#             # Check if credentials is a dictionary and contains 'client_secret'
#             if isinstance(credentials, dict) and 'client_secret' not in credentials:
#                 raise ValueError('Authorized user info is missing the required field: client_secret')
#
#             service = build('calendar', 'v3', credentials=credentials)
#             return service
#
#         except google.auth.exceptions.RefreshError as refresh_error:
#             logging.error(f'Token refresh error: {str(refresh_error)}')
#             raise ValueError('Error refreshing Google Calendar API token')
#
#         except google.auth.exceptions.AuthError as auth_error:
#             logging.error(f'Authentication error: {str(auth_error)}')
#             return render_template('error.html', message='Authentication error. Please re-authenticate.'), 401
#
#         except google.auth.exceptions.TransportError as transport_error:
#             logging.error(f'Transport error: {str(transport_error)}')
#             raise ValueError('Error obtaining Google Calendar API service')
#
#         except HttpError as http_error:
#             if http_error.resp.status == 401:
#                 return render_template('login.html', message='Authentication failed. Please log in again.'), 401
#             elif http_error.resp.status == 403 and 'usageLimits' in str(http_error):
#                 # Handle 403 error due to Calendar usage limits exceeded
#                 logging.warning('Calendar usage limits exceeded. Retrying...')
#                 retry_count += 1
#                 sleep_seconds = 2 ** retry_count
#                 time.sleep(sleep_seconds)
#             else:
#                 logging.error(f'Google Calendar API Error: {http_error}')
#                 raise ValueError(f'Google Calendar API Error: {http_error}')
#
#     raise ValueError('Maximum number of retries reached. Unable to obtain Google Calendar API service.')

def get_google_calendar_service():
    # Define the maximum number of retries
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            credentials = get_google_auth()

            # Check if credentials is a dictionary and contains 'client_secret'
            if not isinstance(credentials, dict) or 'client_secret' not in credentials:
                raise ValueError('Authorized user info is missing the required field: client_secret')

            service = build('calendar', 'v3', credentials=credentials)
            return service

        except google.auth.exceptions.RefreshError as refresh_error:
            logging.error(f'Token refresh error: {str(refresh_error)}')
            raise ValueError('Error refreshing Google Calendar API token')

        except ValueError as value_error:
            if 'client_secret' in str(value_error):
                logging.error(f'Authorized user info is missing the required field: client_secret')
                return render_template('error.html', message='Authorized user info is missing the required field: client_secret'), 500

        except google.auth.exceptions.AuthError as auth_error:
            logging.error(f'Authentication error: {str(auth_error)}')
            return render_template('error.html', message='Authentication error. Please re-authenticate.'), 401

        except google.auth.exceptions.TransportError as transport_error:
            logging.error(f'Transport error: {str(transport_error)}')
            raise ValueError('Error obtaining Google Calendar API service')

        except HttpError as http_error:
            if http_error.resp.status == 401:
                return render_template('login.html', message='Authentication failed. Please log in again.'), 401
            elif http_error.resp.status == 403 and 'usageLimits' in str(http_error):
                # Handle 403 error due to Calendar usage limits exceeded
                logging.warning('Calendar usage limits exceeded. Retrying...')
                retry_count += 1
                sleep_seconds = 2 ** retry_count
                time.sleep(sleep_seconds)
            else:
                logging.error(f'Google Calendar API Error: {http_error}')
                raise ValueError(f'Google Calendar API Error: {http_error}')

    raise ValueError('Maximum number of retries reached. Unable to obtain Google Calendar API service.')

# def get_google_calendar_service():
#     # Define the maximum number of retries
#     max_retries = 5
#     retry_count = 0
#
#     while retry_count < max_retries:
#         try:
#             credentials = get_google_auth()
#             service = build('calendar', 'v3', credentials=credentials)
#             return service
#
#         except google.auth.exceptions.RefreshError as refresh_error:
#             logging.error(f'Token refresh error: {str(refresh_error)}')
#             raise ValueError('Error refreshing Google Calendar API token')
#
#         except google.auth.exceptions.AuthError as auth_error:
#             logging.error(f'Authentication error: {str(auth_error)}')
#             return render_template('error.html', message='Authentication error. Please re-authenticate.'), 401
#
#         except google.auth.exceptions.TransportError as transport_error:
#             logging.error(f'Transport error: {str(transport_error)}')
#             raise ValueError('Error obtaining Google Calendar API service')
#
#         except HttpError as http_error:
#             if http_error.resp.status == 401:
#                 return render_template('login.html', message='Authentication failed. Please log in again.'), 401
#             elif http_error.resp.status == 403 and 'usageLimits' in str(http_error):
#                 # Handle 403 error due to Calendar usage limits exceeded
#                 logging.warning('Calendar usage limits exceeded. Retrying...')
#                 retry_count += 1
#                 sleep_seconds = 2 ** retry_count
#                 time.sleep(sleep_seconds)
#             else:
#                 logging.error(f'Google Calendar API Error: {http_error}')
#                 raise ValueError(f'Google Calendar API Error: {http_error}')
#
#     raise ValueError('Maximum number of retries reached. Unable to obtain Google Calendar API service.')

def store_event_details(user_id, event_id, date, time, title, location, description):
    # Convert date string to datetime object
    date_obj = datetime.strptime(date, '%Y-%m-%d')

    # Check if the event already exists in the database
    existing_event = Appointment.query.filter_by(event_id=event_id).first()

    if existing_event:
        # Update the existing event details if needed
        existing_event.date = date_obj  # Use the datetime object
        existing_event.time = time
        existing_event.title = title
        existing_event.location = location
        existing_event.description = description
        print(f'Existing event: {existing_event}')
    else:
        # Create a new event entry in the database
        new_event = Appointment(
            user_id=user_id,
            event_id=event_id,
            date=date_obj,  # Use the datetime object
            time=time,
            title=title,
            location=location,
            description=description
        )
        print(f"New Events: {new_event}")
        db.session.add(new_event)

    # Commit changes to the database
    db.session.commit()

def convert_to_user_timezone(dt, user_timezone):
    # TODO: obtain the user's timezone from their preferences or profile information.
    utc_dt = dt.replace(tzinfo=pytz.utc)
    user_tz = pytz.timezone(user_timezone)
    user_dt = utc_dt.astimezone(user_tz)
    return user_dt

def send_reminder(user_id, date, time, reminder_offset_minutes, background_tasks: BackgroundTasks):
    # Set the reminder time, ... 30 minutes before the appointment
    reminder_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M') - dt.timedelta(
        minutes=reminder_offset_minutes)

    # Check if it's time to send the reminder
    current_datetime = datetime.utcnow()
    if current_datetime >= reminder_datetime:
        # It's time to send the reminder
        reminder_message = f"Reminder: Your appointment is scheduled for {date} at {time}. Don't forget!"

        # Schedule the actual sending of the reminder in the background
        background_tasks.add_task(send_actual_reminder, user_id, reminder_message)
        return reminder_message
    else:
        # Reminder is not due yet
        logging.info(f"Reminder schedule for {reminder_datetime}")
        return f"Reminder schedule for {reminder_datetime}"
@celery.task
def send_actual_reminder(user_id, reminder_message):
    try:
        app.logger.info(f'Sending reminder to user {user_id} with subject: {reminder_message}')
        print(f"Sending reminder to user {user_id}: {reminder_message}")

        # TODO: add user email to database (user_email)
        # temporary_email = 'terahjones@gmail.com'
        email = get_user_email(user_id)

        # Call the appropriate email-sending function asynchronously
        send_email_with_flask_mail.apply_async(args=[email, "Reminder", reminder_message])
        # ro:
        send_email_with_smtplib.apply_async(args=[email, "Reminder", reminder_message])
    except (smtplib.SMTPException, Exception) as e:
        app.logger.error(f'Failed to send reminder to user {user_id}: {str(e)}')


@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    else:
        return render_template('index.html')


def validate_date_and_time(date, time):
    try:
        # Check if date is in the correct format(YYYY-MM-DD)
        datetime.strptime(date, '%Y-%m-%d')

        # Check if time is in  the correct format(HH:MM)
        datetime.strptime(time, '%H:%M')

        return None  # Validate successful, no error message
    except ValueError as e:
        return str(e)


def validate_future_date(date):
    try:
        # Convert the date string to a datetime object
        date_obj = datetime.strptime(date, '%Y-%m-%d')

        # Get the current date
        current_date = datetime.now()

        # Check if the provided date is in the future
        if date_obj > current_date:
            return None  # Validation successful, no error message
        else:
            return 'Appointment date must be in the future'
    except ValueError as e:
        return str(e)  # Return False if there is an issue parsing the date


CALENDAR_ID = 'primary'
TIME_ZONE = 'UTC'
from datetime import datetime, timezone

def sync_with_calendar(user_id, date, time, title, location, description, background_tasks: BackgroundTasks):
    user = User.query.get(user_id)

    if not user:
        return {'status': 'error', 'message': 'User not found'}

    google_calendar_token = user.get_google_calendar_token()

    if not google_calendar_token:
        app.logger.info(f'user_id: {user_id}, google_calendar_token: {google_calendar_token}')
        return {'status': 'error', 'message': 'Google Calendar token not found'}

    creds = Credentials.from_authorized_user_info(google_calendar_token, SCOPES)
    try:
        service = build('calendar', 'v3', credentials=creds)
        event_datetime = datetime.strptime(f'{date}T{time}', '%Y-%m-%dT%H:%M')

        event_data = {
            'summary': title,
            'location': location,
            'description': description,
            'colorId': 6,
            'start': {
                'dateTime': event_datetime.isoformat(),
                'timeZone': TIME_ZONE,
            },
            'end': {
                'dateTime': event_datetime.isoformat(),
                'timeZone': TIME_ZONE,
            },
            'recurrence': [
                'RRULE:FREQ=DAILY;COUNT=3'
            ],
            'attendees': [
                {'email': 'tj.papajones@gmail.com'},
                {'email': 'example@gmail.com'},
                {'email': 'jtalukwe@kabarak.ac.ke'},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        event = service.events().insert(calendarId=CALENDAR_ID, body=event_data).execute()

        event_id = event['id']
        event_datetime_utc = event_datetime.replace(tzinfo=timezone.utc)

        return {
            'status': 'success',
            'message': f'Google Calendar: Appointment scheduled for {event_datetime_utc} was successfully',
            'event_id': event_id
        }

    except HttpError as error:
        return {
            'status': 'error',
            'message': f'Google Calendar API Error for User {user_id}: {error}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Google Calendar API Error for User {user_id}: {str(e)}'
        }




# def get_google_auth():
#     creds = None
#
#     try:
#         if os.path.exists("token.json"):
#             creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 creds.refresh(Request())
#             else:
#                 flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
#                 creds = flow.run_local_server(port=0)
#
#                 # Save the obtained token to the user's model
#                 if current_user.is_authenticated:
#                     current_user.set_google_calendar_token(creds.to_json())
#
#                 # Write the token to a local file
#                 with open("token.json", "w") as token_file:
#                     token_file.write(creds.to_json())
#
#     except FileNotFoundError as e:
#         logging.error("Token file not found: %s", e)
#     except Exception as e:
#         logging.error("Error in get_google_auth: %s", e)
#
#     return creds


@app.route('/schedule', methods=['POST'])
@login_required
def schedule_appointment():
    try:
        data = request.get_json()

        if 'user_id' in data and data['user_id'] != current_user.id:
            return jsonify({'message': 'Unauthorized to modify appointments for other users'}), 403

        date = data.get('date', '')
        time = data.get('time', '')
        title = data.get('title', '')
        location = data.get('location', '')
        description = data.get('description', '')

        date_error = validate_date_and_time(date, time)
        if date_error:
            return jsonify({'message': f'Invalid date or time format. {date_error}'}), 400

        future_date_error = validate_future_date(date)
        if future_date_error:
            return jsonify({'message': future_date_error}), 400

        calendar_response = sync_with_calendar(current_user.id, date, time, title, location, description, BackgroundTasks())

        if calendar_response['status'] == 'success':
            # Process successful calendar response
            event_id = calendar_response['event_id']
            store_event_details(current_user.id, event_id, date, time, title, location, description)

            reminder_offset_minutes = 10
            send_reminder(current_user.id, date, time, reminder_offset_minutes, BackgroundTasks())

            return jsonify({'message': 'Appointment scheduled successfully'})
        else:
            # Handle error response from calendar
            return jsonify({'message': calendar_response['message']}), 500

    except Exception as e:
        return jsonify({'message': f'Internal server error: {str(e)}'}), 500



# mail config
@shared_task(bind=True, base=AbortableTask)
@celery.task
def send_email_with_smtplib(to, subject, body):
    smtp_server = app.config['MAIL_SERVER']
    smtp_port = app.config['MAIL_PORT']
    smtp_username = app.config['MAIL_USERNAME']
    smtp_password = app.config['MAIL_PASSWORD']
    sender_email = app.config['MAIL_DEFAULT_SENDER']

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = formataddr((f'DigiWave', f'{sender_email}'))
    msg['To'] = to

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, [to], msg.as_string())
        logging.info(f'Email sent using smtplib to {to}')
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f'SMTP Authentication Error: {str(e)}')
    except Exception as e:
        logging.error(f'Failed to send email using smtplib to {to}: {str(e)}', exc_info=True)


@shared_task(bind=True, base=AbortableTask)
@celery.task
def send_email_with_flask_mail(to, subject, body):
    try:
        msg = Message(subject, recipients=[to], body=body)
        mail.send(msg)
        app.logger.info(f'Email sent using Flask-Mail to {to} with subject: {subject}')
        return True  # Indicate successful email sending
    except (smtplib.SMTPException, Exception) as e:
        app.logger.error(f'Failed to send email using Flask-Mail to {to}: {str(e)}')
        return False  # Indicate failed email sending


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
