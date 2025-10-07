# Email setup (SMTP) for Project Nexus

This document shows how to enable real email delivery for the Project Nexus Django app.

By default, the project uses the console email backend for development (emails are printed to the runserver console). To send real emails, set environment variables as shown below and restart the server.

## Basic SMTP (recommended for most providers)

Add the following variables to your environment (or `.env` if you use python-dotenv):

- EMAIL_BACKEND=smtp
- EMAIL_HOST=smtp.example.com
- EMAIL_PORT=587
- EMAIL_HOST_USER=your_smtp_username
- EMAIL_HOST_PASSWORD=your_smtp_password
- EMAIL_USE_TLS=1
- DEFAULT_FROM_EMAIL="noreply@example.com"

Example (.env):

EMAIL_BACKEND=smtp
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.xxxxxxx
EMAIL_USE_TLS=1
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

Notes for popular providers:
- SendGrid (SMTP):
  - Set EMAIL_HOST=smtp.sendgrid.net, EMAIL_HOST_USER=`apikey`, EMAIL_HOST_PASSWORD=`<SENDGRID_API_KEY>`
  - Port 587 with TLS is typical.
- Mailgun (SMTP):
  - Set EMAIL_HOST=smtp.mailgun.org and use the SMTP credentials for your domain.
- Amazon SES (SMTP):
  - Use the SES SMTP credentials, choose port 587 (TLS) or 465 (SSL). If using 465, set EMAIL_USE_SSL=1.

## Testing email delivery

1. Restart Django runserver.
2. Trigger an action that sends email (for example: register a new user via the Swagger UI at `/api/docs/`).
3. If SMTP is configured correctly, you'll receive the verification email at the supplied address.

If things don't work:
- Check the runserver/stderr logs for SMTP errors.
- Try `telnet smtp.example.com 587` from your host to confirm network connectivity to the SMTP host/port.

## Quick local-only test using Python shell

You can test email sending from a Python shell with Django loaded (requires environment variables set):

```powershell
python manage.py shell
```

Then in the shell:

```py
from django.core.mail import send_mail
send_mail('Test', 'This is a test', 'noreply@example.com', ['you@example.com'])
```

If the SMTP backend is configured and reachable, the function will return the number of delivered messages (usually 1).

## Security
- Do not commit real SMTP credentials into the repository. Use environment variables or a secret manager.
- Use TLS where possible and use provider best-practices (API keys, limited-scope credentials).

## Optional: Use transactional email API SDKs
- For better deliverability and features (templates, tracking), use provider SDKs (SendGrid, Mailgun) with HTTP APIs instead of SMTP. That requires adding provider-specific client libraries and wiring them into a custom Django email backend or sending via the provider's SDK from your view/queue tasks.

\n