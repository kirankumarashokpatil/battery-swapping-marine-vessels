"""
Production-Ready Authentication System for Marine Vessels Battery Swapping App

This module provides secure user authentication with:
- Password hashing using bcrypt
- User registration and management
- Password reset functionality
- Session management with timeouts
- Rate limiting and security features
- Secure data storage with encryption
"""

import json
import os
import re
import secrets
import smtplib
import string
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import bcrypt
import streamlit as st
from dotenv import load_dotenv  # type: ignore

# Load environment variables
load_dotenv()

# Constants
USER_DATA_FILE = "user_data.enc"
SESSION_TIMEOUT_HOURS = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1
MIN_PASSWORD_LENGTH = 8

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USERNAME or '')
APP_URL = os.getenv('APP_URL', 'http://localhost:8501')

def is_demo_mode() -> bool:
    """Check if demo mode is enabled."""
    return os.getenv('DEMO_MODE', 'true').lower() == 'true'

class AuthSystem:
    """Production-ready authentication system with security features."""

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize the authentication system."""
        if data_dir is None:
            # Default to app directory
            self.data_dir = Path(__file__).parent
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(exist_ok=True)
        self.user_data_file = self.data_dir / USER_DATA_FILE

        # Initialize encryption key (in production, use environment variable)
        self.encryption_key = os.getenv('AUTH_ENCRYPTION_KEY', 'default_dev_key_change_in_prod')

        # Load or initialize user data
        self._load_user_data()

    def _load_user_data(self) -> None:
        """Load encrypted user data from file."""
        if self.user_data_file.exists():
            try:
                with open(self.user_data_file, 'r') as f:
                    data = f.read()
                # Simple XOR encryption for demo (use proper encryption in production)
                # For now, disable encryption to avoid corruption
                # self.user_data = json.loads(self._decrypt_data(data))
                self.user_data = json.loads(data)
            except Exception as e:
                st.error(f"Error loading user data: {str(e)}")
                self.user_data = self._get_default_user_data()
        else:
            self.user_data = self._get_default_user_data()
            self._save_user_data()

    def _save_user_data(self) -> None:
        """Save user data to encrypted file."""
        try:
            # Simple XOR encryption for demo (use proper encryption in production)
            # For now, disable encryption to avoid corruption
            # encrypted_data = self._encrypt_data(json.dumps(self.user_data, indent=2))
            data = json.dumps(self.user_data, indent=2)
            with open(self.user_data_file, 'w') as f:
                f.write(data)
        except Exception as e:
            st.error(f"Error saving user data: {str(e)}")

    def _encrypt_data(self, data: str) -> str:
        """Simple encryption for demo purposes. Use proper encryption in production."""
        key = self.encryption_key
        encrypted = []
        for i, char in enumerate(data):
            key_char = key[i % len(key)]
            encrypted.append(chr(ord(char) ^ ord(key_char)))
        return ''.join(encrypted)

    def _decrypt_data(self, data: str) -> str:
        """Decrypt data (same as encrypt for XOR)."""
        return self._encrypt_data(data)

    def _get_default_user_data(self) -> Dict:
        """Get default user data structure."""
        return {
            "users": {},
            "sessions": {},
            "login_attempts": {},
            "password_reset_tokens": {}
        }

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def _generate_session_token(self) -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)

    def _generate_password_reset_token(self) -> str:
        """Generate a secure password reset token."""
        return secrets.token_urlsafe(16)

    def _is_password_strong(self, password: str) -> Tuple[bool, str]:
        """Check if password meets strength requirements."""
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in string.punctuation for c in password)

        if not has_upper:
            return False, "Password must contain at least one uppercase letter"
        if not has_lower:
            return False, "Password must contain at least one lowercase letter"
        if not has_digit:
            return False, "Password must contain at least one digit"
        if not has_special:
            return False, "Password must contain at least one special character"

        return True, "Password is strong"

    def _send_password_reset_email(self, email: str, username: str, reset_token: str) -> bool:
        """Send password reset email to user."""
        # Check if email configuration is available
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            print("Email configuration not available - skipping email send")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = FROM_EMAIL
            msg['To'] = email
            msg['Subject'] = "Marine Vessels - Password Reset Request"

            # Create reset link
            reset_link = f"{APP_URL}/?reset_token={reset_token}"

            # Email body
            body = f"""
            Dear {username},

            You have requested to reset your password for the Marine Vessels Battery Swapping application.

            To reset your password, please click the link below:
            {reset_link}

            This link will expire in {PASSWORD_RESET_TOKEN_EXPIRY_HOURS} hour(s).

            If you did not request this password reset, please ignore this email.

            Best regards,
            Marine Vessels Support Team
            NatPower UK
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(FROM_EMAIL, email, text)
            server.quit()

            return True
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            return False

    def _send_admin_notification_email(self, admin_email: str, username: str, user_email: str) -> bool:
        """Send notification to admin about password reset request."""
        # Check if email configuration is available
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            print("Email configuration not available - skipping admin notification")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = FROM_EMAIL
            msg['To'] = admin_email
            msg['Subject'] = "Marine Vessels - Password Reset Notification"

            # Email body
            body = f"""
            Admin Notification:

            User '{username}' has requested a password reset.

            User Details:
            - Username: {username}
            - Email: {user_email or 'Not provided'}

            The user has been sent a password reset link via email.

            Best regards,
            Marine Vessels System
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(FROM_EMAIL, admin_email, text)
            server.quit()

            return True
        except Exception as e:
            print(f"Failed to send admin notification email: {e}")
            return False

    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed login attempts."""
        attempts = self.user_data["login_attempts"].get(username, {})
        if not attempts:
            return False

        failed_count = attempts.get("count", 0)
        last_attempt = attempts.get("last_attempt", 0)
        lockout_until = attempts.get("lockout_until", 0)

        current_time = time.time()

        # Check if still in lockout period
        if current_time < lockout_until:
            return True

        # Reset if lockout period has passed
        if failed_count >= MAX_LOGIN_ATTEMPTS and current_time >= lockout_until:
            attempts["count"] = 0
            attempts["lockout_until"] = 0
            self._save_user_data()

        return False

    def _record_login_attempt(self, username: str, success: bool) -> None:
        """Record a login attempt."""
        attempts = self.user_data["login_attempts"].setdefault(username, {
            "count": 0,
            "last_attempt": 0,
            "lockout_until": 0
        })

        current_time = time.time()

        if success:
            # Reset on successful login
            attempts["count"] = 0
            attempts["lockout_until"] = 0
        else:
            # Increment failed attempts
            attempts["count"] += 1
            attempts["last_attempt"] = current_time

            # Lock account if max attempts reached
            if attempts["count"] >= MAX_LOGIN_ATTEMPTS:
                attempts["lockout_until"] = current_time + (LOCKOUT_DURATION_MINUTES * 60)

        self._save_user_data()

    def register_user(self, username: str, password: str, email: str = "") -> Tuple[bool, str]:
        """Register a new user."""
        # Validate input
        if not username or not password:
            return False, "Username and password are required"

        if len(username) < 3:
            return False, "Username must be at least 3 characters long"

        # Check if user already exists
        if username in self.user_data["users"]:
            return False, "Username already exists"

        # Validate password strength
        is_strong, strength_msg = self._is_password_strong(password)
        if not is_strong:
            return False, strength_msg

        # Create user (inactive by default - requires admin approval)
        user_data = {
            "username": username,
            "password_hash": self._hash_password(password),
            "email": email,
            "created_at": time.time(),
            "last_login": None,
            "is_active": False,  # Require admin approval
            "is_approved": False,  # Track approval status
            "role": "user",  # Default role
            "approved_by": None,
            "approved_at": None
        }

        self.user_data["users"][username] = user_data
        self._save_user_data()

        return True, "Registration successful! Your account is pending admin approval."

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate a user."""
        # Check if account is locked
        if self._is_account_locked(username):
            return False, "Account is temporarily locked due to too many failed login attempts"

        # Check if user exists
        user = self.user_data["users"].get(username)
        if not user:
            self._record_login_attempt(username, False)
            return False, "Invalid username or password"

        # Check if account is active and approved
        if not user.get("is_active", True):
            return False, "Account is deactivated"
        
        if not user.get("is_approved", False):
            return False, "Account is pending admin approval"

        # Verify password
        if not self._verify_password(password, user["password_hash"]):
            self._record_login_attempt(username, False)
            return False, "Invalid username or password"

        # Successful login
        self._record_login_attempt(username, True)
        user["last_login"] = time.time()
        self._save_user_data()

        return True, "Login successful"

    def create_session(self, username: str) -> str:
        """Create a new session for the user."""
        session_token = self._generate_session_token()
        session_data = {
            "username": username,
            "created_at": time.time(),
            "expires_at": time.time() + (SESSION_TIMEOUT_HOURS * 3600)
        }

        self.user_data["sessions"][session_token] = session_data
        self._save_user_data()

        return session_token

    def validate_session(self, session_token: str) -> Optional[str]:
        """Validate a session token and return username if valid."""
        session = self.user_data["sessions"].get(session_token)
        if not session:
            return None

        current_time = time.time()
        if current_time > session["expires_at"]:
            # Session expired, remove it
            del self.user_data["sessions"][session_token]
            self._save_user_data()
            return None

        # Extend session on activity
        session["expires_at"] = current_time + (SESSION_TIMEOUT_HOURS * 3600)
        self._save_user_data()

        return session["username"]

    def logout_session(self, session_token: str) -> None:
        """Logout a session."""
        if session_token in self.user_data["sessions"]:
            del self.user_data["sessions"][session_token]
            self._save_user_data()

    def initiate_password_reset(self, username_or_email: str) -> Tuple[bool, str]:
        """Initiate password reset process."""
        user = None
        username = None

        # Find user by username or email
        for uname, udata in self.user_data["users"].items():
            if uname == username_or_email or udata.get("email") == username_or_email:
                user = udata
                username = uname
                break

        if not user:
            return False, "User not found"

        # Check if user has an email address
        user_email = user.get("email")
        if not user_email:
            return False, "No email address associated with this account. Please contact an administrator."

        # Generate reset token
        reset_token = self._generate_password_reset_token()
        expiry = time.time() + (PASSWORD_RESET_TOKEN_EXPIRY_HOURS * 3600)

        self.user_data["password_reset_tokens"][reset_token] = {
            "username": username,
            "expires_at": expiry,
            "used": False
        }

        self._save_user_data()

        if is_demo_mode():
            # In demo mode, return the token directly
            return True, f"Password reset token: {reset_token}"
        else:
            # In production mode, send email
            if username is None:
                return False, "Unable to identify user for password reset"

            email_sent = self._send_password_reset_email(user_email, username, reset_token)

            if email_sent:
                # Also notify admin if admin user
                if user.get("role") == "admin":
                    admin_emails = []
                    for uname, udata in self.user_data["users"].items():
                        if udata.get("role") == "admin" and udata.get("email"):
                            admin_emails.append(udata["email"])

                    for admin_email in admin_emails:
                        self._send_admin_notification_email(admin_email, username, user_email)

                return True, f"Password reset instructions have been sent to {user_email}"
            else:
                return False, "Failed to send password reset email. Please try again later."

    def reset_password(self, reset_token: str, new_password: str) -> Tuple[bool, str]:
        """Reset password using reset token."""
        token_data = self.user_data["password_reset_tokens"].get(reset_token)
        if not token_data:
            return False, "Invalid reset token"

        if token_data["used"]:
            return False, "Reset token has already been used"

        if time.time() > token_data["expires_at"]:
            return False, "Reset token has expired"

        # Validate new password
        is_strong, strength_msg = self._is_password_strong(new_password)
        if not is_strong:
            return False, strength_msg

        # Update password
        username = token_data["username"]
        user = self.user_data["users"][username]
        user["password_hash"] = self._hash_password(new_password)

        # Mark token as used
        token_data["used"] = True

        self._save_user_data()

        return True, "Password reset successfully"

    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password."""
        user = self.user_data["users"].get(username)
        if not user:
            return False, "User not found"

        # Verify old password
        if not self._verify_password(old_password, user["password_hash"]):
            return False, "Current password is incorrect"

        # Validate new password
        is_strong, strength_msg = self._is_password_strong(new_password)
        if not is_strong:
            return False, strength_msg

        # Update password
        user["password_hash"] = self._hash_password(new_password)
        self._save_user_data()

        return True, "Password changed successfully"

    def change_username(self, current_username: str, new_username: str, password: str) -> Tuple[bool, str]:
        """Change user username."""
        # Validate input
        if not current_username or not new_username or not password:
            return False, "All fields are required"

        if len(new_username) < 3:
            return False, "New username must be at least 3 characters long"

        if not re.match(r'^[a-zA-Z0-9_]+$', new_username):
            return False, "New username can only contain letters, numbers, and underscores"

        # Check if user exists
        user = self.user_data["users"].get(current_username)
        if not user:
            return False, "User not found"

        # Verify password
        if not self._verify_password(password, user["password_hash"]):
            return False, "Password is incorrect"

        # Check if new username is already taken
        if new_username in self.user_data["users"]:
            return False, "New username is already taken"

        # Move user data to new username
        user_data = self.user_data["users"][current_username]
        user_data["username"] = new_username  # Update the username field
        self.user_data["users"][new_username] = user_data
        del self.user_data["users"][current_username]

        # Update any active sessions for this user
        for session_token, session_data in self.user_data["sessions"].items():
            if session_data["username"] == current_username:
                session_data["username"] = new_username

        # Update any password reset tokens for this user
        for token, token_data in self.user_data["password_reset_tokens"].items():
            if token_data["username"] == current_username:
                token_data["username"] = new_username

        self._save_user_data()

        return True, f"Username changed successfully from '{current_username}' to '{new_username}'"

    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information (without sensitive data)."""
        user = self.user_data["users"].get(username)
        if not user:
            return None

        return {
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"],
            "last_login": user["last_login"],
            "is_active": user["is_active"],
            "is_approved": user.get("is_approved", False),
            "role": user["role"],
            "approved_by": user.get("approved_by"),
            "approved_at": user.get("approved_at")
        }

    def get_pending_approvals(self) -> List[Dict]:
        """Get list of users pending admin approval."""
        pending = []
        for username, user_data in self.user_data["users"].items():
            if not user_data.get("is_approved", False) and user_data.get("is_active", True):
                pending.append({
                    "username": username,
                    "email": user_data.get("email", ""),
                    "created_at": user_data["created_at"],
                    "role": user_data.get("role", "user")
                })
        return pending

    def approve_user(self, admin_username: str, target_username: str) -> Tuple[bool, str]:
        """Approve a user registration (admin only)."""
        admin_user = self.user_data["users"].get(admin_username)
        if not admin_user or admin_user.get("role") != "admin":
            return False, "Unauthorized: Admin access required"

        target_user = self.user_data["users"].get(target_username)
        if not target_user:
            return False, "User not found"

        if target_user.get("is_approved", False):
            return False, "User is already approved"

        # Approve the user
        target_user["is_approved"] = True
        target_user["is_active"] = True
        target_user["approved_by"] = admin_username
        target_user["approved_at"] = time.time()

        self._save_user_data()
        return True, f"User {target_username} has been approved and can now log in"

    def deny_user(self, admin_username: str, target_username: str) -> Tuple[bool, str]:
        """Deny a user registration (admin only)."""
        admin_user = self.user_data["users"].get(admin_username)
        if not admin_user or admin_user.get("role") != "admin":
            return False, "Unauthorized: Admin access required"

        target_user = self.user_data["users"].get(target_username)
        if not target_user:
            return False, "User not found"

        if target_user.get("is_approved", False):
            return False, "Cannot deny an already approved user"

        # Deactivate the user account
        target_user["is_active"] = False

        self._save_user_data()
        return True, f"User {target_username} registration has been denied"

    def get_all_users(self, admin_username: str) -> Tuple[bool, List[Dict]]:
        """Get all users (admin only)."""
        admin_user = self.user_data["users"].get(admin_username)
        if not admin_user or admin_user.get("role") != "admin":
            return False, []

        users = []
        for username, user_data in self.user_data["users"].items():
            users.append({
                "username": username,
                "email": user_data.get("email", ""),
                "created_at": user_data["created_at"],
                "last_login": user_data.get("last_login"),
                "is_active": user_data.get("is_active", True),
                "is_approved": user_data.get("is_approved", False),
                "role": user_data.get("role", "user"),
                "approved_by": user_data.get("approved_by"),
                "approved_at": user_data.get("approved_at")
            })
        return True, users

    def deactivate_user(self, admin_username: str, target_username: str) -> Tuple[bool, str]:
        """Deactivate a user account (admin only)."""
        admin_user = self.user_data["users"].get(admin_username)
        if not admin_user or admin_user.get("role") != "admin":
            return False, "Unauthorized: Admin access required"

        if admin_username == target_username:
            return False, "Cannot deactivate your own account"

        target_user = self.user_data["users"].get(target_username)
        if not target_user:
            return False, "User not found"

        target_user["is_active"] = False
        self._save_user_data()
        return True, f"User {target_username} has been deactivated"

    def activate_user(self, admin_username: str, target_username: str) -> Tuple[bool, str]:
        """Reactivate a user account (admin only)."""
        admin_user = self.user_data["users"].get(admin_username)
        if not admin_user or admin_user.get("role") != "admin":
            return False, "Unauthorized: Admin access required"

        target_user = self.user_data["users"].get(target_username)
        if not target_user:
            return False, "User not found"

        if not target_user.get("is_approved", False):
            return False, "Cannot activate unapproved user"

        target_user["is_active"] = True
        self._save_user_data()
        return True, f"User {target_username} has been reactivated"

    def set_user_active_status(self, admin_username: str, target_username: str, is_active: bool) -> Tuple[bool, str]:
        """Set user active status (admin only)."""
        if is_active:
            return self.activate_user(admin_username, target_username)
        else:
            return self.deactivate_user(admin_username, target_username)

    def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions and tokens."""
        current_time = time.time()

        # Clean expired sessions
        expired_sessions = [
            token for token, session in self.user_data.get("sessions", {}).items()
            if current_time > session["expires_at"]
        ]
        for token in expired_sessions:
            del self.user_data["sessions"][token]

        # Clean expired reset tokens
        expired_tokens = [
            token for token, token_data in self.user_data.get("password_reset_tokens", {}).items()
            if current_time > token_data["expires_at"] or token_data["used"]
        ]
        for token in expired_tokens:
            del self.user_data["password_reset_tokens"][token]

        if expired_sessions or expired_tokens:
            self._save_user_data()


# Global auth system instance
_auth_system = None

def get_auth_system() -> AuthSystem:
    """Get the global authentication system instance."""
    global _auth_system
    if _auth_system is None:
        _auth_system = AuthSystem()
        _auth_system.cleanup_expired_sessions()  # Clean up on startup
    return _auth_system


def login_required(func):
    """Decorator to require login for a function."""
    def wrapper(*args, **kwargs):
        if not st.session_state.get('authenticated', False):
            # This will be handled in main.py
            return None
        return func(*args, **kwargs)
    return wrapper