import base64
import logging
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from openai import OpenAI

from config import Config


class ScreenshotStockChecker:
    """Stock checker using screenshots and GPT Vision"""

    def __init__(self):
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.driver = None

    def setup_driver(self):
        """Setup Chrome driver with optimized options"""
        if self.driver:
            return

        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        chrome_options.add_argument(f"--user-agent={user_agent}")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logging.info("✅ Chrome driver initialized successfully")
        except Exception as e:
            logging.error(f"❌ Failed to initialize Chrome driver: {e}")
            raise

    def cleanup_driver(self):
        """Clean up the driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def take_screenshot(self, url: str) -> str:
        """Take screenshot of URL and return base64 encoded image"""
        try:
            self.setup_driver()

            logging.info(f"📸 Taking screenshot of {url}")
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Additional wait for dynamic content
            import time

            time.sleep(3)

            # Take screenshot
            screenshot = self.driver.get_screenshot_as_png()

            # Convert to PIL Image and resize if needed
            image = Image.open(BytesIO(screenshot))

            # Resize if too large (OpenAI has size limits)
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Convert back to bytes
            img_buffer = BytesIO()
            image.save(img_buffer, format="PNG", optimize=True)
            img_bytes = img_buffer.getvalue()

            # Encode to base64
            base64_image = base64.b64encode(img_bytes).decode("utf-8")

            logging.info(
                f"✅ Screenshot taken successfully ({len(base64_image)} chars)"
            )
            return base64_image

        except Exception as e:
            logging.error(f"❌ Screenshot failed for {url}: {e}")
            raise

    def analyze_stock_with_gpt(self, base64_image: str, url: str) -> dict:
        """Analyze screenshot using GPT Vision to determine stock status"""
        try:
            prompt = """
            Analyze this e-commerce product page screenshot and determine:
            
            1. Is the product IN STOCK or OUT OF STOCK?
            2. What is the product name?
            3. What is the price?
            4. What specific visual elements indicate stock status?
            
            Look for:
            - "Add to Cart" buttons
            - "Buy Now" buttons  
            - "Pick One to Shake" buttons (PopMart specific)
            - "Buy Multiple Boxes" buttons
            - "Out of Stock" messages
            - "Sold Out" indicators
            - Price displays
            - Product availability text
            
            Respond in JSON format:
            {
                "in_stock": true/false,
                "product_name": "Product Name",
                "price": "$XX.XX",
                "confidence": 0.95,
                "reasoning": "Explanation of what you see that indicates stock status",
                "elements_found": ["list", "of", "key", "elements", "detected"]
            }
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # GPT-4 with vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=500,
                temperature=0.1,  # Low temperature for consistent analysis
            )

            analysis_text = response.choices[0].message.content.strip()

            # Try to parse JSON response
            import json

            try:
                # Extract JSON from response (GPT sometimes adds extra text)
                start = analysis_text.find("{")
                end = analysis_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = analysis_text[start:end]
                    analysis = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")

            except (json.JSONDecodeError, ValueError) as e:
                # Fallback: try to extract basic info from text
                logging.warning(f"Failed to parse JSON from GPT response: {e}")
                analysis = {
                    "in_stock": "in stock" in analysis_text.lower()
                    or "add to cart" in analysis_text.lower(),
                    "product_name": "Unknown",
                    "price": "Unknown",
                    "confidence": 0.5,
                    "reasoning": analysis_text,
                    "elements_found": [],
                }

            logging.info(f"🤖 GPT Analysis: {analysis}")
            return analysis

        except Exception as e:
            logging.error(f"❌ GPT Vision analysis failed: {e}")
            raise

    def check_stock_with_screenshot(self, url: str) -> tuple[bool, dict]:
        """Main method to check stock using screenshot + GPT Vision"""
        try:
            # Take screenshot
            base64_image = self.take_screenshot(url)

            # Analyze with GPT
            analysis = self.analyze_stock_with_gpt(base64_image, url)

            # Extract stock status and product info
            in_stock = analysis.get("in_stock", False)
            product_info = {
                "name": analysis.get("product_name", "Unknown"),
                "price": analysis.get("price", "Unknown"),
                "confidence": analysis.get("confidence", 0.0),
                "reasoning": analysis.get("reasoning", ""),
                "elements_found": analysis.get("elements_found", []),
                "analysis_method": "screenshot_gpt_vision",
            }

            logging.info(f"📊 Stock Check Result: {url} - In Stock: {in_stock}")
            return in_stock, product_info

        except Exception as e:
            logging.error(f"❌ Screenshot stock check failed for {url}: {e}")
            return False, {
                "name": "Unknown",
                "price": "Unknown",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}",
                "elements_found": [],
                "analysis_method": "screenshot_gpt_vision_failed",
            }
        finally:
            # Always cleanup
            self.cleanup_driver()


# Test function
def test_screenshot_checker():
    """Test the screenshot checker with PopMart URL"""
    checker = ScreenshotStockChecker()

    test_url = "https://www.popmart.com/us/pop-now/set/228"
    print("🧪 Testing screenshot checker with: " + test_url)

    try:
        in_stock, product_info = checker.check_stock_with_screenshot(test_url)

        print(f"\n📊 RESULTS:")
        print(f"In Stock: {in_stock}")
        print(f"Product: {product_info.get('name', 'Unknown')}")
        print(f"Price: {product_info.get('price', 'Unknown')}")
        print(f"Confidence: {product_info.get('confidence', 0.0)}")
        print(f"Reasoning: {product_info.get('reasoning', 'None')}")
        print(f"Elements Found: {product_info.get('elements_found', [])}")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_screenshot_checker()
