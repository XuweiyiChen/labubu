import requests
import logging
import time
from datetime import datetime
from bs4 import BeautifulSoup
from openai import OpenAI
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from config import Config
from database import DatabaseManager
from notifiers import NotificationManager

try:
    from screenshot_checker import ScreenshotStockChecker

    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False
    logging.warning("Screenshot checker not available - selenium dependencies missing")


class ProductInfo:
    """Data class for product information"""

    def __init__(
        self,
        name: str = None,
        price: str = None,
        image_url: str = None,
        availability: str = None,
    ):
        self.name = name
        self.price = price
        self.image_url = image_url
        self.availability = availability
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "price": self.price,
            "image_url": self.image_url,
            "availability": self.availability,
            "last_updated": self.last_updated.isoformat(),
        }


class StockMonitor:
    """Main stock monitoring class"""

    def __init__(self):
        self.db = DatabaseManager()
        self.notification_manager = NotificationManager()
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.last_stock_status = {}

        # Add default URLs to database
        for url in Config.get_urls():
            self.db.add_monitor_url(url)

    def extract_product_info(self, soup: BeautifulSoup, url: str) -> ProductInfo:
        """Extract product information from the page"""
        info = ProductInfo()

        try:
            # Try multiple selectors for product name
            name_selectors = [
                "h1.product-title",
                'h1[data-testid="product-title"]',
                ".product-name",
                "h1",
                ".title",
            ]

            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    info.name = name_elem.get_text().strip()
                    break

            # Try multiple selectors for price
            price_selectors = [
                ".product-price",
                ".price",
                '[data-testid="product-price"]',
                ".current-price",
                ".sale-price",
            ]

            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    info.price = price_elem.get_text().strip()
                    break

            # Try to find product image
            img_selectors = [
                ".product-image img",
                ".hero-image img",
                ".main-image img",
                'img[data-testid="product-image"]',
            ]

            for selector in img_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    img_src = img_elem.get("src") or img_elem.get("data-src")
                    if img_src:
                        # Convert relative URL to absolute
                        info.image_url = urljoin(url, img_src)
                        break

            # Check availability text
            availability_selectors = [
                ".availability",
                ".stock-status",
                ".product-availability",
            ]

            for selector in availability_selectors:
                avail_elem = soup.select_one(selector)
                if avail_elem:
                    info.availability = avail_elem.get_text().strip()
                    break

        except Exception as e:
            logging.warning(f"Error extracting product info from {url}: {e}")

        return info

    def check_stock(
        self, url: str, use_screenshot: bool = False
    ) -> tuple[bool, ProductInfo]:
        """Check if product is in stock and return stock status + product info"""

        # Try screenshot method if enabled and available
        if use_screenshot and SCREENSHOT_AVAILABLE:
            try:
                logging.info(f"📸 Using screenshot method for {url}")
                screenshot_checker = ScreenshotStockChecker()
                in_stock, screenshot_info = (
                    screenshot_checker.check_stock_with_screenshot(url)
                )

                # Convert screenshot info to ProductInfo
                product_info = ProductInfo(
                    name=screenshot_info.get("name"),
                    price=screenshot_info.get("price"),
                    availability=f"Screenshot analysis (confidence: {screenshot_info.get('confidence', 0)})",
                )

                logging.info(
                    f"📊 Screenshot analysis: stock={in_stock}, confidence={screenshot_info.get('confidence', 0)}"
                )
                return in_stock, product_info

            except Exception as e:
                logging.warning(
                    f"📸 Screenshot method failed for {url}: {e}, falling back to HTML parsing"
                )

        # Fallback to traditional HTML parsing method
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(
                url, headers=headers, timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            product_info = self.extract_product_info(soup, url)

            # Check for stock indicators
            in_stock = False

            # Method 1: Check for any button with stock-related text
            all_buttons = soup.find_all(["button", "a", "div"])
            stock_button_phrases = [
                "add to cart",
                "buy now",
                "purchase",
                "pick one to shake",
                "buy multiple boxes",
                "add to bag",
                "shop now",
                "get it now",
                "buy",
                "cart",
                "shake",
                "pick one",
            ]

            for btn in all_buttons:
                btn_text = btn.get_text().strip().lower()
                if btn_text and any(
                    phrase in btn_text for phrase in stock_button_phrases
                ):
                    # Check if button is not disabled
                    if not btn.get("disabled") and "disabled" not in btn.get(
                        "class", []
                    ):
                        logging.debug(f"Found stock button: '{btn_text.strip()}'")
                        in_stock = True
                        break

            # Method 2: Check for specific PopMart stock indicators in page text
            if not in_stock:
                page_text = soup.get_text().lower()
                popmart_stock_indicators = [
                    "pick one to shake",
                    "buy multiple boxes",
                    "add to cart",
                    "in stock",
                    "available now",
                    "buy now",
                ]

                for indicator in popmart_stock_indicators:
                    if indicator in page_text:
                        logging.debug(f"Found stock indicator in text: '{indicator}'")
                        in_stock = True
                        break

            # Method 3: Check availability text
            if not in_stock:
                availability_texts = (
                    [product_info.availability] if product_info.availability else []
                )

                # Add more availability indicators
                stock_indicators = soup.select(
                    ".stock-status, .availability, .product-status"
                )
                for indicator in stock_indicators:
                    availability_texts.append(indicator.get_text().strip().lower())

                for text in availability_texts:
                    if text and any(
                        phrase in text
                        for phrase in ["in stock", "available", "add to cart"]
                    ):
                        in_stock = True
                        break
                    elif any(
                        phrase in text
                        for phrase in ["out of stock", "sold out", "unavailable"]
                    ):
                        in_stock = False
                        break

            # Method 4: Check if page exists and doesn't show 404/error
            if soup.select("h1"):  # Basic check if page loaded properly
                page_text = soup.get_text().lower()
                if "page not found" in page_text or "404" in page_text:
                    in_stock = False

            logging.debug(
                f"Stock check for {url}: in_stock={in_stock}, "
                f"product={product_info.name}"
            )

            return in_stock, product_info

        except requests.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            return False, ProductInfo()
        except Exception as e:
            logging.error(f"Stock check failed for {url}: {e}")
            return False, ProductInfo()

    def generate_ai_message(self, url: str, product_info: ProductInfo) -> str:
        """Generate AI-powered notification message"""
        try:
            product_name = product_info.name or "Labubu product"
            price = product_info.price or "Unknown price"

            prompt = f"""
            A PopMart {product_name} (price: {price}) just came back in stock! 
            Create an exciting, urgent notification message that will motivate someone 
            to buy it immediately. Keep it under 100 words and include emojis.
            URL: {url}
            """

            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an enthusiastic shopping assistant who helps people get limited edition collectibles.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.8,
            )

            ai_message = response.choices[0].message.content.strip()
            logging.info(f"Generated AI message: {ai_message}")
            return ai_message

        except Exception as e:
            logging.error(f"Failed to generate AI message: {e}")
            return f"🎉 Great news! {product_info.name or 'Your monitored item'} is back in stock! Get it now before it sells out again! 🛒✨"

    def process_restock_alert(self, url: str, product_info: ProductInfo):
        """Process and send restock alerts"""
        try:
            # Generate AI message
            ai_message = self.generate_ai_message(url, product_info)

            # Send notifications
            notification_results = self.notification_manager.send_restock_alert(
                url, ai_message, product_info.to_dict()
            )

            # Log notification attempts
            for notifier_type, success in notification_results.items():
                status = "success" if success else "failed"
                self.db.log_notification(url, notifier_type, status, ai_message)

            logging.info(
                f"Restock alert processed for {url}. "
                f"Notifications: {notification_results}"
            )

        except Exception as e:
            logging.error(f"Failed to process restock alert for {url}: {e}")

    def monitor_single_url(self, url: str):
        """Monitor a single URL for stock changes"""
        try:
            self.db.update_last_checked(url)

            in_stock, product_info = self.check_stock(url)

            # Log the stock event
            self.db.log_stock_event(
                url, in_stock, product_info.name, product_info.price
            )

            # Check if this is a new restock (was out of stock, now in stock)
            was_in_stock = self.last_stock_status.get(url, False)

            if in_stock and not was_in_stock:
                logging.info(f"🎉 RESTOCK DETECTED! {url}")
                self.process_restock_alert(url, product_info)

            # Update last known status
            self.last_stock_status[url] = in_stock

            status_emoji = "✅" if in_stock else "❌"
            logging.info(
                f"{status_emoji} {url} - Stock: {in_stock} - "
                f"Product: {product_info.name or 'Unknown'}"
            )

        except Exception as e:
            logging.error(f"Error monitoring {url}: {e}")

    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle for all URLs"""
        monitor_urls = self.db.get_monitor_urls()

        if not monitor_urls:
            logging.warning("No URLs to monitor!")
            return

        logging.info(f"Starting monitoring cycle for {len(monitor_urls)} URLs")

        for url_data in monitor_urls:
            url = url_data["url"]
            try:
                self.monitor_single_url(url)
                # Small delay between requests to be respectful
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error in monitoring cycle for {url}: {e}")

        logging.info("Monitoring cycle completed")

    def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        logging.info("🚀 Starting Labubu Monitor")
        logging.info(f"Check interval: {Config.CHECK_INTERVAL} seconds")
        logging.info(
            f"Enabled notifiers: {self.notification_manager.get_enabled_notifiers()}"
        )

        try:
            while True:
                self.run_monitoring_cycle()
                logging.info(f"💤 Sleeping for {Config.CHECK_INTERVAL} seconds...")
                time.sleep(Config.CHECK_INTERVAL)

        except KeyboardInterrupt:
            logging.info("🛑 Monitoring stopped by user")
        except Exception as e:
            logging.error(f"Fatal error in monitoring loop: {e}")
            raise
