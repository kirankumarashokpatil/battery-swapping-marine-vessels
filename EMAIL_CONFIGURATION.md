# Email Configuration Guide

This guide explains how to configure email functionality for password reset in production mode.

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Email Configuration for Password Reset
# SMTP server settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Email settings
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Marine Vessels Battery Swapping App

# Application settings
APP_URL=http://localhost:8501
DEMO_MODE=false
```

## Gmail Configuration

For Gmail accounts:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this 16-character password as `SMTP_PASSWORD`

## Other Email Providers

### Outlook/Hotmail
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### Yahoo
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
```

## Testing Email Configuration

1. Set `DEMO_MODE=false` in your `.env` file
2. Run the application
3. Try the password reset functionality
4. Check that emails are sent successfully

## Security Notes

- Never commit the `.env` file to version control
- Use app passwords instead of your main email password
- Consider using a dedicated email service for production (SendGrid, Mailgun, etc.)
- The app will gracefully fall back to demo mode if email configuration is missing

## Demo Mode

When `DEMO_MODE=true` (default), password reset tokens are displayed directly in the UI instead of being emailed. This is useful for development and testing.