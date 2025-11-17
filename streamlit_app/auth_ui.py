"""
Authentication UI Components for Marine Vessels Battery Swapping App

This module provides Streamlit UI components for:
- User login
- User registration
- Password reset
- Profile management
"""

import re
from datetime import datetime
import streamlit as st
from typing import Callable, Optional

from auth_system import get_auth_system


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def show_login_page() -> None:
    """Display the login page for authentication."""
    st.title("🔐 Marine Vessels Battery Swapping - Login")
    st.markdown("---")

    st.markdown("""
    ### Welcome to the Marine Vessels Battery Swapping Optimizer

    Please log in to access the optimization tool.
    """)

    # Initialize session state for auth mode
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'

    # Mode selector
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔑 Login", use_container_width=True,
                    type="primary" if st.session_state.auth_mode == 'login' else "secondary"):
            st.session_state.auth_mode = 'login'
            st.rerun()
    with col2:
        if st.button("📝 Register", use_container_width=True,
                    type="primary" if st.session_state.auth_mode == 'register' else "secondary"):
            st.session_state.auth_mode = 'register'
            st.rerun()
    with col3:
        if st.button("🔄 Reset Password", use_container_width=True,
                    type="primary" if st.session_state.auth_mode == 'reset' else "secondary"):
            st.session_state.auth_mode = 'reset'
            st.rerun()

    st.markdown("---")

    auth_system = get_auth_system()

    if st.session_state.auth_mode == 'login':
        _show_login_form(auth_system)
    elif st.session_state.auth_mode == 'register':
        _show_registration_form(auth_system)
    elif st.session_state.auth_mode == 'reset':
        _show_password_reset_form(auth_system)


def _show_login_form(auth_system) -> None:
    """Display the login form."""
    st.subheader("🔑 Login Credentials")

    with st.form("login_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            help="Your registered username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="Your account password"
        )

        login_button = st.form_submit_button(
            "🚀 Login",
            type="primary",
            use_container_width=True,
            help="Click to authenticate"
        )

        if login_button:
            if not username or not password:
                st.error("❌ Please enter both username and password.")
                return

            with st.spinner("Authenticating..."):
                success, message = auth_system.authenticate_user(username, password)

            if success:
                # Create session
                session_token = auth_system.create_session(username)

                # Update session state
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.session_token = session_token

                st.success("✅ Login successful! Redirecting...")
                st.rerun()
            else:
                st.error(f"❌ {message}")

    st.markdown("---")
    st.markdown("""
    **Need an account?** Click "Register" above to create one.

    **Forgot your password?** Click "Reset Password" above.
    """)


def _show_registration_form(auth_system) -> None:
    """Display the user registration form."""
    st.subheader("📝 Create New Account")

    with st.form("registration_form"):
        username = st.text_input(
            "Username",
            placeholder="Choose a username",
            help="3-20 characters, letters, numbers, and underscores only"
        )

        email = st.text_input(
            "Email (Optional)",
            placeholder="your.email@example.com",
            help="For password recovery and notifications"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a strong password",
            help="Minimum 8 characters with uppercase, lowercase, number, and special character"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm your password",
            help="Re-enter your password"
        )

        agree_terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            help="You must agree to continue"
        )

        register_button = st.form_submit_button(
            "📝 Register Account",
            type="primary",
            use_container_width=True,
            help="Create your account"
        )

        if register_button:
            # Validation
            errors = []

            if not username:
                errors.append("Username is required")
            elif len(username) < 3:
                errors.append("Username must be at least 3 characters long")
            elif not re.match(r'^[a-zA-Z0-9_]+$', username):
                errors.append("Username can only contain letters, numbers, and underscores")

            if email and not validate_email(email):
                errors.append("Please enter a valid email address")

            if not password:
                errors.append("Password is required")
            elif password != confirm_password:
                errors.append("Passwords do not match")

            if not agree_terms:
                errors.append("You must agree to the Terms of Service")

            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
                return

            # Attempt registration
            with st.spinner("Creating account..."):
                success, message = auth_system.register_user(username, password, email)

            if success:
                st.success("✅ Registration successful!")
                st.info("Your account has been created and is pending admin approval. You will be able to log in once approved.")
                st.session_state.auth_mode = 'login'
                st.rerun()
            else:
                st.error(f"❌ {message}")

    st.markdown("---")
    st.markdown("""
    **Already have an account?** Click "Login" above.

    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character (!@#$%^&*)
    """)


def _show_password_reset_form(auth_system) -> None:
    """Display the password reset form."""
    st.subheader("🔄 Reset Password")

    # Initialize reset state
    if 'reset_step' not in st.session_state:
        st.session_state.reset_step = 'request'

    if st.session_state.reset_step == 'request':
        _show_password_reset_request(auth_system)
    elif st.session_state.reset_step == 'reset':
        _show_password_reset_confirm(auth_system)


def _show_password_reset_request(auth_system) -> None:
    """Show password reset request form."""
    st.write("Enter your username or email address to receive a password reset token.")

    # Check if we just successfully requested a token
    if 'reset_token_display' in st.session_state and st.session_state.reset_token_display:
        st.success("✅ Password reset initiated!")
        st.info(f"**Reset Token:** `{st.session_state.reset_token_display}`")
        st.warning("⚠️ **Demo Mode**: In production, this token would be sent to your email.")

        # Clear the display flag so it doesn't show again on refresh
        if st.button("✅ I have copied the token - Continue to Reset", type="primary"):
            st.session_state.reset_step = 'reset'
            del st.session_state.reset_token_display
            st.rerun()
        return

    # Check if we just sent an email in production mode
    if 'reset_email_sent' in st.session_state and st.session_state.reset_email_sent:
        st.success("✅ Password reset email sent!")
        st.info("Please check your email for password reset instructions.")
        st.info("The reset link will expire in 24 hours.")

        # Clear the flag and go to login
        if st.button("🔑 Back to Login", type="primary"):
            st.session_state.auth_mode = 'login'
            st.session_state.reset_step = 'request'
            del st.session_state.reset_email_sent
            st.rerun()
        return

    with st.form("reset_request_form"):
        username_or_email = st.text_input(
            "Username or Email",
            placeholder="Enter your username or email",
            help="We'll send a reset token to your email or display it here"
        )

        request_button = st.form_submit_button(
            "📧 Request Reset Token",
            type="primary",
            use_container_width=True
        )

        if request_button:
            if not username_or_email:
                st.error("❌ Please enter your username or email.")
                return

            with st.spinner("Processing request..."):
                success, message = auth_system.initiate_password_reset(username_or_email)

            if success:
                # Check if it's demo mode (token returned) or production mode (email sent)
                if "Password reset token:" in message:
                    # Demo mode - extract and display token
                    token = message.split(': ')[1]
                    st.session_state.reset_token = token
                    st.session_state.reset_token_display = token
                    st.rerun()  # This will show the token above
                else:
                    # Production mode - email sent
                    st.session_state.reset_email_sent = True
                    st.rerun()  # This will show the email sent message above
            else:
                st.error(f"❌ {message}")

    st.markdown("---")
    st.markdown("""
    **Remember your password?** Click "Login" above.

    **Need to register?** Click "Register" above.
    """)


def _show_password_reset_confirm(auth_system) -> None:
    """Show password reset confirmation form."""
    st.write("Enter the reset token and your new password.")

    # Pre-fill token if available
    default_token = st.session_state.get('reset_token', '')

    with st.form("reset_confirm_form"):
        reset_token = st.text_input(
            "Reset Token",
            value=default_token,
            placeholder="Enter the reset token",
            help="Token received via email or shown above"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Enter your new password",
            help="Minimum 8 characters with mixed case, numbers, and special characters"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            placeholder="Confirm your new password",
            help="Re-enter your new password"
        )

        reset_button = st.form_submit_button(
            "🔄 Reset Password",
            type="primary",
            use_container_width=True
        )

        if reset_button:
            errors = []

            if not reset_token:
                errors.append("Reset token is required")
            if not new_password:
                errors.append("New password is required")
            elif new_password != confirm_password:
                errors.append("Passwords do not match")

            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
                return

            with st.spinner("Resetting password..."):
                success, message = auth_system.reset_password(reset_token, new_password)

            if success:
                st.success("✅ Password reset successfully!")
                st.info("You can now log in with your new password.")
                # Clear reset state
                if 'reset_token' in st.session_state:
                    del st.session_state.reset_token
                if 'reset_token_display' in st.session_state:
                    del st.session_state.reset_token_display
                st.session_state.reset_step = 'request'
                st.session_state.auth_mode = 'login'
                st.rerun()
            else:
                st.error(f"❌ {message}")

    # Back button
    if st.button("⬅️ Back to Reset Request"):
        st.session_state.reset_step = 'request'
        # Clear any stored tokens when going back
        if 'reset_token_display' in st.session_state:
            del st.session_state.reset_token_display
        st.rerun()


def show_user_profile() -> None:
    """Display user profile management."""
    st.header("👤 User Profile")

    auth_system = get_auth_system()
    username = st.session_state.get('username')

    if not username:
        st.error("No user logged in")
        return

    user_info = auth_system.get_user_info(username)
    if not user_info:
        st.error("User information not found")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Account Information")
        st.write(f"**Username:** {user_info['username']}")
        st.write(f"**Email:** {user_info['email'] or 'Not provided'}")
        st.write(f"**Role:** {user_info['role']}")
        st.write(f"**Account Status:** {'Active' if user_info['is_active'] else 'Inactive'}")
        st.write(f"**Approval Status:** {'Approved' if user_info.get('is_approved', False) else 'Pending Approval'}")

        if user_info['created_at']:
            created_date = datetime.fromtimestamp(user_info['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            st.write(f"**Account Created:** {created_date}")

        if user_info['last_login']:
            last_login_date = datetime.fromtimestamp(user_info['last_login']).strftime('%Y-%m-%d %H:%M:%S')
            st.write(f"**Last Login:** {last_login_date}")

        if user_info.get('approved_at') and user_info.get('approved_by'):
            approved_date = datetime.fromtimestamp(user_info['approved_at']).strftime('%Y-%m-%d %H:%M:%S')
            st.write(f"**Approved By:** {user_info['approved_by']} on {approved_date}")

    with col2:
        st.subheader("🔧 Account Management")

        # Change password section
        with st.expander("🔑 Change Password", expanded=False):
            _show_change_password_form(auth_system, username)

        # Change username section
        with st.expander("👤 Change Username", expanded=False):
            _show_change_username_form(auth_system, username)

        # Admin management section (only for admins)
        if user_info.get('role') == 'admin':
            with st.expander("👑 Admin Panel", expanded=False):
                _show_admin_panel(auth_system, username)

        # Security settings
        with st.expander("🔒 Security Settings", expanded=False):
            st.info("Security features are automatically managed by the system.")
            st.write("✅ Password hashing with bcrypt")
            st.write("✅ Account lockout after failed attempts")
            st.write("✅ Session timeout after 8 hours")
            st.write("✅ Secure password requirements")


def _show_change_password_form(auth_system, username: str) -> None:
    """Show change password form."""
    with st.form("change_password_form"):
        current_password = st.text_input(
            "Current Password",
            type="password",
            help="Enter your current password"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            help="Enter your new password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            help="Confirm your new password"
        )

        change_button = st.form_submit_button(
            "🔄 Change Password",
            type="primary"
        )

        if change_button:
            errors = []

            if not current_password:
                errors.append("Current password is required")
            if not new_password:
                errors.append("New password is required")
            elif new_password != confirm_password:
                errors.append("New passwords do not match")

            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
                return

            with st.spinner("Changing password..."):
                success, message = auth_system.change_password(username, current_password, new_password)

            if success:
                st.success("✅ Password changed successfully!")
                st.info("Please use your new password for future logins.")
            else:
                st.error(f"❌ {message}")


def _show_change_username_form(auth_system, username: str) -> None:
    """Show change username form."""
    with st.form("change_username_form"):
        new_username = st.text_input(
            "New Username",
            placeholder="Enter your new username",
            help="3-20 characters, letters, numbers, and underscores only"
        )

        password = st.text_input(
            "Current Password",
            type="password",
            help="Enter your current password to confirm"
        )

        change_button = st.form_submit_button(
            "👤 Change Username",
            type="primary"
        )

        if change_button:
            errors = []

            if not new_username:
                errors.append("New username is required")
            if not password:
                errors.append("Current password is required")

            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
                return

            with st.spinner("Changing username..."):
                success, message = auth_system.change_username(username, new_username, password)

            if success:
                st.success("✅ Username changed successfully!")
                st.info(f"Your username has been changed from '{username}' to '{new_username}'")
                st.warning("⚠️ You will need to log in again with your new username.")
                # Update session state
                st.session_state.username = new_username
                # Don't logout immediately - let user see the success message
                st.info("🔄 Please log out and log back in to see your new username.")
            else:
                st.error(f"❌ {message}")


def show_logout_button() -> None:
    """Display logout button in sidebar."""
    auth_system = get_auth_system()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"👤 **{st.session_state.get('username', 'Unknown')}**")
    with col2:
        if st.button("🚪 Logout", key="logout_button", help="Sign out"):
            # Logout session
            session_token = st.session_state.get('session_token')
            if session_token:
                auth_system.logout_session(session_token)

            # Clear session state
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.session_token = None

            st.rerun()


def _show_admin_panel(auth_system, admin_username: str) -> None:
    """Show admin management panel for user approval and management."""
    st.write("### 👥 User Management")

    # Get all users
    success, all_users = auth_system.get_all_users(admin_username)

    if not success:
        st.error("❌ Unable to access user management. Admin privileges required.")
        return

    if not all_users:
        st.info("No users found in the system.")
        return

    # Separate users by status
    pending_users = []
    approved_users = []
    admin_users = []

    for user_info in all_users:
        username = user_info['username']
        if user_info.get('role') == 'admin':
            admin_users.append(user_info)
        elif user_info.get('is_approved', False):
            approved_users.append(user_info)
        else:
            pending_users.append(user_info)

    # Pending approvals section
    if pending_users:
        st.subheader("⏳ Pending Approvals")
        st.write(f"**{len(pending_users)} user(s) waiting for approval**")

        for user_info in pending_users:
            username = user_info['username']
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**{username}**")
                    if user_info.get('email'):
                        st.write(f"📧 {user_info['email']}")
                    if user_info.get('created_at'):
                        created_date = datetime.fromtimestamp(user_info['created_at']).strftime('%Y-%m-%d %H:%M')
                        st.write(f"📅 Created: {created_date}")

                with col2:
                    if st.button("✅ Approve", key=f"approve_{username}", help=f"Approve user {username}"):
                        with st.spinner(f"Approving {username}..."):
                            success, message = auth_system.approve_user(admin_username, username)
                        if success:
                            st.success(f"✅ {username} has been approved!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to approve {username}: {message}")

                with col3:
                    if st.button("❌ Deny", key=f"deny_{username}", help=f"Deny user {username}"):
                        with st.spinner(f"Denying {username}..."):
                            success, message = auth_system.deny_user(admin_username, username)
                        if success:
                            st.success(f"❌ {username} has been denied!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to deny {username}: {message}")

                st.divider()

    # Approved users section
    if approved_users:
        st.subheader("✅ Approved Users")
        st.write(f"**{len(approved_users)} approved user(s)**")

        for user_info in approved_users:
            username = user_info['username']
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**{username}** ({user_info.get('role', 'user')})")
                    if user_info.get('email'):
                        st.write(f"📧 {user_info['email']}")
                    if user_info.get('approved_at') and user_info.get('approved_by'):
                        approved_date = datetime.fromtimestamp(user_info['approved_at']).strftime('%Y-%m-%d %H:%M')
                        st.write(f"✅ Approved by {user_info['approved_by']} on {approved_date}")

                with col2:
                    status = "Active" if user_info.get('is_active', True) else "Inactive"
                    st.write(f"Status: {status}")

                with col3:
                    if username != admin_username:  # Can't deactivate yourself
                        action = "Deactivate" if user_info.get('is_active', True) else "Activate"
                        button_type = "secondary" if user_info.get('is_active', True) else "primary"

                        if st.button(action, key=f"toggle_{username}", help=f"{action} user {username}", type=button_type):
                            new_status = not user_info.get('is_active', True)
                            with st.spinner(f"{'Deactivating' if not new_status else 'Activating'} {username}..."):
                                success, message = auth_system.set_user_active_status(admin_username, username, new_status)
                            if success:
                                st.success(f"✅ {username} has been {'deactivated' if not new_status else 'activated'}!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to update {username}: {message}")

                st.divider()

    # Admin users section
    if admin_users:
        st.subheader("👑 Admin Users")
        st.write(f"**{len(admin_users)} admin user(s)**")

        for user_info in admin_users:
            username = user_info['username']
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**{username}** (Administrator)")
                    if user_info.get('email'):
                        st.write(f"📧 {user_info['email']}")
                    if user_info.get('created_at'):
                        created_date = datetime.fromtimestamp(user_info['created_at']).strftime('%Y-%m-%d %H:%M')
                        st.write(f"📅 Created: {created_date}")

                with col2:
                    status = "Active" if user_info.get('is_active', True) else "Inactive"
                    st.write(f"Status: {status}")

                st.divider()

    # System statistics
    st.subheader("📊 System Statistics")
    total_users = len(all_users)
    active_users = sum(1 for u in all_users if u.get('is_active', True))
    approved_count = sum(1 for u in all_users if u.get('is_approved', False))
    pending_count = total_users - approved_count

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", total_users)
    with col2:
        st.metric("Active Users", active_users)
    with col3:
        st.metric("Approved", approved_count)
    with col4:
        st.metric("Pending", pending_count)