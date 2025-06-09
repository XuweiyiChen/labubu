#!/usr/bin/env python3
"""
Labubu Monitor - Advanced stock monitoring for PopMart collectibles
Main entry point for the application
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config import Config
from monitor import StockMonitor
from web_dashboard import app


def setup_logging():
    """Setup logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(f"logs/{Config.LOG_FILE}"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Reduce noise from some third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def validate_config():
    """Validate configuration and show warnings"""
    errors = Config.validate()

    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix these errors before running the monitor.")
        return False

    print("✅ Configuration validated successfully")
    return True


def run_monitor():
    """Run the stock monitor"""
    print("🚀 Starting Labubu Monitor")
    print(f"📡 Monitoring URLs: {len(Config.get_urls())}")
    print(f"⏱️  Check interval: {Config.CHECK_INTERVAL} seconds")
    print(f"🔔 Notification methods: {get_enabled_notifications()}")
    print("-" * 50)

    monitor = StockMonitor()
    monitor.run_continuous_monitoring()


def run_web():
    """Run the web dashboard"""
    print("🌐 Starting Labubu Monitor Web Dashboard")
    print(f"🔗 URL: http://{Config.WEB_HOST}:{Config.WEB_PORT}")
    print(f"📊 Dashboard will show monitoring statistics and history")
    print("-" * 50)

    app.run(host=Config.WEB_HOST, port=Config.WEB_PORT, debug=False, use_reloader=False)


def get_enabled_notifications():
    """Get list of enabled notification methods"""
    methods = []
    if Config.ENABLE_EMAIL:
        methods.append("Email")
    if Config.ENABLE_DISCORD:
        methods.append("Discord")
    if Config.ENABLE_WEBHOOK:
        methods.append("Webhook")
    return methods if methods else ["None"]


def show_status():
    """Show current configuration status"""
    print("📋 Labubu Monitor Configuration Status")
    print("=" * 50)

    print(f"📁 Database: {Config.DB_PATH}")
    print(f"📝 Log file: {Config.LOG_FILE}")
    print(f"⏱️  Check interval: {Config.CHECK_INTERVAL} seconds")
    print(f"🌐 Web dashboard: {Config.WEB_HOST}:{Config.WEB_PORT}")

    print(f"\n📡 Monitored URLs ({len(Config.get_urls())}):")
    for i, url in enumerate(Config.get_urls(), 1):
        print(f"  {i}. {url}")

    print(f"\n🔔 Notifications:")
    notifications = get_enabled_notifications()
    for method in notifications:
        print(f"  ✅ {method}")

    # Show OpenAI status
    api_key_status = "✅ Configured" if Config.OPENAI_API_KEY else "❌ Not configured"
    print(f"\n🤖 AI Messages: {api_key_status}")

    print(f"\n🔧 To modify settings, edit environment variables or config.py")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Labubu Monitor - Advanced stock monitoring for PopMart collectibles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py monitor          # Run stock monitoring
  python main.py web             # Run web dashboard  
  python main.py status          # Show configuration status
  
Environment Variables:
  OPENAI_API_KEY                 # Required: Your OpenAI API key
  MONITOR_URLS                   # URLs to monitor (comma-separated)
  CHECK_INTERVAL                 # Check interval in seconds (default: 30)
  ENABLE_EMAIL                   # Enable email notifications (true/false)
  EMAIL_USERNAME                 # Email username for notifications
  EMAIL_PASSWORD                 # Email password for notifications  
  EMAIL_TO                       # Recipient emails (comma-separated)
  ENABLE_DISCORD                 # Enable Discord notifications (true/false)
  DISCORD_WEBHOOK_URL            # Discord webhook URL
        """,
    )

    parser.add_argument(
        "command", choices=["monitor", "web", "status"], help="Command to run"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Override log level if debug is requested
    if args.debug:
        Config.LOG_LEVEL = "DEBUG"

    # Setup logging
    setup_logging()

    # Show status
    if args.command == "status":
        show_status()
        return

    # Validate configuration for monitor/web commands
    if not validate_config():
        sys.exit(1)

    try:
        if args.command == "monitor":
            run_monitor()
        elif args.command == "web":
            run_web()
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
