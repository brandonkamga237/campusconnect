"""Envoi d'emails par SMTP (Mailpit en dev). L'envoi se fait en tâche de fond : un SMTP lent
ou absent ne bloque pas la requête, l'erreur est seulement journalisée."""
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

log = logging.getLogger("auth-service.mail")


def send_mail(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.mail_host, settings.mail_port, timeout=10) as smtp:
            if settings.mail_starttls:
                smtp.starttls()
            if settings.mail_username:
                smtp.login(settings.mail_username, settings.mail_password)
            smtp.send_message(msg)
        log.info("Email '%s' envoyé à %s", subject, to)
    except (OSError, smtplib.SMTPException) as exc:
        log.error("Échec d'envoi de l'email '%s' à %s : %s", subject, to, exc)


def verification_email(to: str, token: str) -> tuple[str, str, str]:
    link = f"{settings.frontend_url}/verify-email?token={token}"
    body = (
        "Bienvenue sur CampusConnect !\n\n"
        f"Confirmez votre adresse email en ouvrant ce lien :\n{link}\n\n"
        f"Ou utilisez ce code avec POST /api/auth/verify-email :\n{token}\n\n"
        f"Ce lien expire dans {settings.email_verification_hours} h."
    )
    return to, "Confirmez votre adresse email", body


def password_reset_email(to: str, token: str) -> tuple[str, str, str]:
    link = f"{settings.frontend_url}/reset-password?token={token}"
    body = (
        "Vous avez demandé à réinitialiser votre mot de passe CampusConnect.\n\n"
        f"Ouvrez ce lien pour choisir un nouveau mot de passe :\n{link}\n\n"
        f"Ou utilisez ce code avec POST /api/auth/password/reset :\n{token}\n\n"
        f"Ce lien expire dans {settings.password_reset_minutes} min. "
        "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
    )
    return to, "Réinitialisation de votre mot de passe", body
