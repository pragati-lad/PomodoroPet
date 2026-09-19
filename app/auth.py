import logging
import sys
import resend
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer
from app import db
from app.models import User
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


def generate_verification_token(email):
    """Generate a timed token for email verification."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='email-verify')


def verify_token(token, max_age=3600):
    """Verify a token and return the email, or None if invalid/expired."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return s.loads(token, salt='email-verify', max_age=max_age)
    except Exception:
        return None


def send_verification_email(user):
    """Send a verification email with a tokenized link via Resend."""
    token = generate_verification_token(user.email)
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    resend.api_key = current_app.config['RESEND_API_KEY']
    try:
        resend.Emails.send({
            "from": current_app.config['MAIL_FROM'],
            "to": [user.email],
            "subject": "Verify your PomoPet account",
            "text": (
                f"Hi {user.username},\n\n"
                f"Click the link below to verify your email:\n"
                f"{verify_url}\n\n"
                f"This link expires in 1 hour.\n\n"
                f"- PomoPet"
            ),
        })
        print(f"[EMAIL] Sent to {user.email}", file=sys.stderr)
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {user.email}: {e}", file=sys.stderr)
        raise


def validate_password_strength(password):
    """Validate password meets strength requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, 'Password must be at least 8 characters'

    if not any(c.isupper() for c in password):
        return False, 'Password must contain at least one uppercase letter'

    if not any(c.islower() for c in password):
        return False, 'Password must contain at least one lowercase letter'

    if not any(c.isdigit() for c in password):
        return False, 'Password must contain at least one number'

    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, 'Password must contain at least one special character (!@#$%^&* etc.)'

    return True, None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))

        if not user.email_verified:
            flash('Please verify your email before logging in. Check your inbox for the verification link.', 'error')
            return redirect(url_for('auth.login'))

        login_user(user, remember=True)

        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.dashboard')

        return redirect(next_page)

    return render_template('login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('auth.signup'))

        if len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return redirect(url_for('auth.signup'))

        # Validate password strength
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('auth.signup'))

        if password != password_confirm:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.signup'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.signup'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.signup'))

        # Create new user (email_verified defaults to False)
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Send verification email
        try:
            send_verification_email(user)
            flash('Account created! Please check your email to verify your account.', 'success')
        except Exception as e:
            flash(f'Account created but email failed: {e}', 'error')

        return redirect(url_for('auth.check_email', email=email))

    return render_template('signup.html')


@auth_bp.route('/check-email')
def check_email():
    """Show 'check your email' page after signup."""
    email = request.args.get('email', '')
    return render_template('verify_email.html', email=email)


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify a user's email via token link."""
    email = verify_token(token)
    if email is None:
        flash('The verification link is invalid or has expired.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if user is None:
        flash('No account found for this email.', 'error')
        return redirect(url_for('auth.login'))

    if user.email_verified:
        flash('Email already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    user.email_verified = True
    db.session.commit()

    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification')
def resend_verification():
    """Resend the verification email."""
    email = request.args.get('email', '').strip().lower()
    if not email:
        flash('No email address provided.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if user is None:
        # Don't reveal whether the email exists
        flash('If an account exists with that email, a new verification link has been sent.', 'info')
        return redirect(url_for('auth.check_email', email=email))

    if user.email_verified:
        flash('Email already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    send_verification_email(user)
    flash('A new verification link has been sent to your email.', 'success')
    return redirect(url_for('auth.check_email', email=email))


@auth_bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Delete user account permanently"""
    if request.method == 'POST':
        password = request.form.get('password', '')

        if not password:
            flash('Please enter your password to confirm deletion', 'error')
            return redirect(url_for('auth.delete_account'))

        # Verify password
        if not current_user.check_password(password):
            flash('Incorrect password. Account not deleted.', 'error')
            return redirect(url_for('auth.delete_account'))

        # Delete user (cascade will delete cat and study sessions automatically)
        username = current_user.username
        db.session.delete(current_user)
        db.session.commit()

        logout_user()
        flash(f'Account "{username}" has been permanently deleted. Goodbye!', 'info')
        return redirect(url_for('main.index'))

    return render_template('delete_account.html')


@auth_bp.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('main.index'))
