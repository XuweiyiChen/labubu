import smtplib
import requests
import logging
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
from config import Config


class BaseNotifier(ABC):
    """Abstract base class for all notifiers"""

    @abstractmethod
    def send_notification(
        self, message: str, url: str, product_info: Dict = None
    ) -> bool:
        """Send a notification with the given message"""
        pass

    @abstractmethod
    def get_notification_type(self) -> str:
        """Return the type of this notifier"""
        pass


class EmailNotifier(BaseNotifier):
    """Email notification handler"""

    def __init__(self):
        self.smtp_server = Config.EMAIL_SMTP_SERVER
        self.smtp_port = Config.EMAIL_SMTP_PORT
        self.username = Config.EMAIL_USERNAME
        self.password = Config.EMAIL_PASSWORD
        self.recipients = Config.EMAIL_TO

    def send_notification(
        self, message: str, url: str, product_info: Dict = None
    ) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = ", ".join(self.recipients)
            msg["Subject"] = "🎉 Labubu Restock Alert!"

            # Create HTML email body
            html_body = f"""
            <html>
            <body>
                <h2>🧸 Labubu Restock Alert! 🧸</h2>
                <p><strong>Great news!</strong> The item you're monitoring is back in stock!</p>
                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <p><strong>Product:</strong> {product_info.get('name', 'Unknown') if product_info else 'Unknown'}</p>
                    <p><strong>Price:</strong> {product_info.get('price', 'N/A') if product_info else 'N/A'}</p>
                    <p><strong>URL:</strong> <a href="{url}">{url}</a></p>
                </div>
                <p><strong>Action required:</strong> Click the link above to purchase now!</p>
                <p><em>AI Message:</em> {message}</p>
                <hr>
                <p style="font-size: 12px; color: #666;">
                    Sent by Labubu Monitor at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logging.info(f"Email notification sent successfully to {self.recipients}")
            return True

        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")
            return False

    def get_notification_type(self) -> str:
        return "email"


class DiscordNotifier(BaseNotifier):
    """Discord webhook notification handler"""

    def __init__(self):
        self.webhook_url = Config.DISCORD_WEBHOOK_URL

    def send_notification(
        self, message: str, url: str, product_info: Dict = None
    ) -> bool:
        """Send Discord notification"""
        try:
            embed = {
                "title": "🧸 Labubu Restock Alert!",
                "description": "The item you're monitoring is back in stock!",
                "color": 0x00FF00,  # Green color
                "fields": [
                    {
                        "name": "Product",
                        "value": (
                            product_info.get("name", "Unknown")
                            if product_info
                            else "Unknown"
                        ),
                        "inline": True,
                    },
                    {
                        "name": "Price",
                        "value": (
                            product_info.get("price", "N/A") if product_info else "N/A"
                        ),
                        "inline": True,
                    },
                    {
                        "name": "Link",
                        "value": f"[Click here to buy!]({url})",
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": f"Labubu Monitor • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                },
            }

            if product_info and product_info.get("image_url"):
                embed["thumbnail"] = {"url": product_info["image_url"]}

            payload = {"content": f"@everyone {message}", "embeds": [embed]}

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logging.info("Discord notification sent successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to send Discord notification: {e}")
            return False

    def get_notification_type(self) -> str:
        return "discord"


class WebhookNotifier(BaseNotifier):
    """Generic webhook notification handler"""

    def __init__(self):
        self.webhook_url = Config.WEBHOOK_URL

    def send_notification(
        self, message: str, url: str, product_info: Dict = None
    ) -> bool:
        """Send webhook notification"""
        try:
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": "restock_alert",
                "url": url,
                "message": message,
                "product_info": product_info or {},
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()

            logging.info("Webhook notification sent successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to send webhook notification: {e}")
            return False

    def get_notification_type(self) -> str:
        return "webhook"


class SlackNotifier(BaseNotifier):
    """Slack webhook notification handler"""

    def __init__(self):
        self.webhook_url = Config.SLACK_WEBHOOK_URL

    def send_notification(
        self, message: str, url: str, product_info: Dict = None
    ) -> bool:
        """Send Slack notification"""
        try:
            # Create rich Slack message blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🧸 Labubu Restock Alert! 🧸",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Great news!* The item you're monitoring is back in stock!\n\n*AI Message:* {message}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Product:*\n{product_info.get('name', 'Unknown') if product_info else 'Unknown'}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Price:*\n{product_info.get('price', 'N/A') if product_info else 'N/A'}",
                        },
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "🛒 Buy Now!"},
                            "url": url,
                            "style": "primary",
                        }
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Sent by Labubu Monitor • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        }
                    ],
                },
            ]

            # Add thumbnail if available
            if product_info and product_info.get("image_url"):
                blocks.insert(
                    2,
                    {
                        "type": "image",
                        "image_url": product_info["image_url"],
                        "alt_text": "Product Image",
                    },
                )

            payload = {"text": f"🧸 Labubu Restock Alert!", "blocks": blocks}

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logging.info("Slack notification sent successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to send Slack notification: {e}")
            return False

    def get_notification_type(self) -> str:
        return "slack"


class NotificationManager:
    """Manages all notification types"""

    def __init__(self):
        self.notifiers: List[BaseNotifier] = []
        self._initialize_notifiers()

    def _initialize_notifiers(self):
        """Initialize enabled notifiers"""
        if Config.ENABLE_EMAIL and Config.EMAIL_USERNAME and Config.EMAIL_TO:
            self.notifiers.append(EmailNotifier())
            logging.info("Email notifier enabled")

        if Config.ENABLE_DISCORD and Config.DISCORD_WEBHOOK_URL:
            self.notifiers.append(DiscordNotifier())
            logging.info("Discord notifier enabled")

        if Config.ENABLE_WEBHOOK and Config.WEBHOOK_URL:
            self.notifiers.append(WebhookNotifier())
            logging.info("Webhook notifier enabled")

        if Config.ENABLE_SLACK and Config.SLACK_WEBHOOK_URL:
            self.notifiers.append(SlackNotifier())
            logging.info("Slack notifier enabled")

        if not self.notifiers:
            logging.warning("No notifiers enabled!")

    def send_restock_alert(
        self, url: str, ai_message: str, product_info: Dict = None
    ) -> Dict[str, bool]:
        """Send restock alert through all enabled notifiers"""
        results = {}

        for notifier in self.notifiers:
            try:
                success = notifier.send_notification(ai_message, url, product_info)
                results[notifier.get_notification_type()] = success
            except Exception as e:
                logging.error(
                    f"Error in {notifier.get_notification_type()} notifier: {e}"
                )
                results[notifier.get_notification_type()] = False

        return results

    def get_enabled_notifiers(self) -> List[str]:
        """Get list of enabled notifier types"""
        return [notifier.get_notification_type() for notifier in self.notifiers]
