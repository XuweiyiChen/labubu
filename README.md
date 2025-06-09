# 🧸 Labubu Monitor

An advanced stock monitoring system for PopMart Labubu collectibles with AI-powered notifications, multiple alert channels, and a beautiful web dashboard.

## ✨ Features

### 🔍 **Smart Stock Monitoring**
- Real-time stock checking with intelligent product detection
- Multiple detection methods (Add to Cart buttons, availability text, etc.)
- Automatic product information extraction (name, price, images)
- Configurable check intervals

### 🤖 **AI-Powered Notifications**
- OpenAI GPT integration for engaging notification messages
- Personalized alerts based on product information
- Enthusiastic and urgent messaging to motivate quick action

### 📱 **Multiple Notification Channels**
- **Email**: Rich HTML emails with product details and images
- **Discord**: Embedded messages with @everyone mentions
- **Webhooks**: Generic API integration for custom systems
- **Extensible**: Easy to add new notification methods

### 📊 **Web Dashboard**
- Real-time monitoring status and statistics
- Historical data visualization
- Manual stock checking
- URL management interface  
- Notification success tracking

### 🗄️ **Advanced Database**
- SQLite database for all historical data
- Stock events, notifications, and URL management
- Performance analytics and success rate tracking
- Easy data export and analysis

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd labubu

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```bash
# Required: Your OpenAI API key
OPENAI_API_KEY=sk-your-api-key-here

# URLs to monitor (comma-separated)
MONITOR_URLS=https://www.popmart.com/us/products/1898/THE-MONSTERS-Let's-Checkmate-Series-Vinyl-Plush-Doll

# Optional: Enable email notifications
ENABLE_EMAIL=true
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=your_notifications@gmail.com

# Optional: Enable Discord notifications  
ENABLE_DISCORD=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
```

### 3. Run the Monitor

```bash
# Check configuration
python main.py status

# Start monitoring
python main.py monitor

# Or run the web dashboard
python main.py web
```

## 📖 Detailed Usage

### Command Line Interface

```bash
# Show current configuration and status
python main.py status

# Run continuous stock monitoring
python main.py monitor

# Run web dashboard on http://localhost:8080
python main.py web

# Enable debug logging
python main.py monitor --debug
```

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key | - |
| `MONITOR_URLS` | ✅ | Comma-separated URLs to monitor | - |
| `CHECK_INTERVAL` | ❌ | Check interval in seconds | 30 |
| `REQUEST_TIMEOUT` | ❌ | HTTP request timeout | 10 |
| `ENABLE_EMAIL` | ❌ | Enable email notifications | false |
| `EMAIL_USERNAME` | ❌ | SMTP username | - |
| `EMAIL_PASSWORD` | ❌ | SMTP password (use app passwords) | - |
| `EMAIL_TO` | ❌ | Recipient emails (comma-separated) | - |
| `ENABLE_DISCORD` | ❌ | Enable Discord notifications | false |
| `DISCORD_WEBHOOK_URL` | ❌ | Discord webhook URL | - |
| `WEB_PORT` | ❌ | Web dashboard port | 8080 |

### Web Dashboard

Access the dashboard at `http://localhost:8080` to:

- 📊 View real-time monitoring status
- 📈 See historical stock data and trends  
- 🔔 Check notification success rates
- ⚙️ Manage monitored URLs
- 🧪 Test stock checking manually

### Setting Up Notifications

#### Email (Gmail)
1. Enable 2-factor authentication on your Gmail account
2. Generate an app password: https://support.google.com/accounts/answer/185833
3. Use your Gmail address as `EMAIL_USERNAME`
4. Use the app password as `EMAIL_PASSWORD`

#### Discord
1. Create a Discord webhook in your server
2. Copy the webhook URL
3. Set `DISCORD_WEBHOOK_URL` in your environment

## 🏗️ Architecture

```
labubu/
├── main.py              # Main entry point
├── config.py            # Configuration management
├── database.py          # Database operations
├── monitor.py           # Core monitoring logic
├── notifiers.py         # Notification systems
├── web_dashboard.py     # Flask web interface
├── requirements.txt     # Dependencies
├── env.example         # Environment template
└── README.md           # This file
```

### Key Components

- **StockMonitor**: Core monitoring engine with intelligent stock detection
- **DatabaseManager**: SQLite database operations and analytics
- **NotificationManager**: Multi-channel notification system
- **Config**: Environment-based configuration management
- **Web Dashboard**: Flask-based monitoring interface

## 🔧 Customization

### Adding New Notification Methods

1. Create a new notifier class in `notifiers.py`:

```python
class MyCustomNotifier(BaseNotifier):
    def send_notification(self, message: str, url: str, product_info: Dict = None) -> bool:
        # Your notification logic here
        pass
    
    def get_notification_type(self) -> str:
        return "my_custom"
```

2. Add it to the `NotificationManager`:

```python
if Config.ENABLE_MY_CUSTOM:
    self.notifiers.append(MyCustomNotifier())
```

### Extending Stock Detection

Modify `StockMonitor.check_stock()` to add new detection methods:

```python
# Add your custom stock detection logic
if not in_stock:
    # Custom detection method
    if soup.select('.my-custom-selector'):
        in_stock = True
```

## 🐛 Troubleshooting

### Common Issues

**"Unable to import" errors**
```bash
pip install -r requirements.txt
```

**OpenAI API errors**
- Verify your API key is correct
- Check your OpenAI account has credits
- Ensure the API key has proper permissions

**Email notifications not working**
- Use app passwords for Gmail (not your regular password)
- Check SMTP settings for other email providers
- Verify firewall allows outbound SMTP connections

**Stock detection not working**
- Check if the website structure has changed
- Enable debug logging: `--debug`
- Test manually via web dashboard

### Debug Mode

Enable detailed logging:

```bash
python main.py monitor --debug
```

This will show:
- HTTP request/response details
- Stock detection logic steps
- Database operations
- Notification attempts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📜 License

This project is for educational purposes. Please respect PopMart's terms of service and use responsibly.

## ⚠️ Disclaimer

This tool is for personal use only. Please:
- Respect website rate limits
- Don't overload servers with frequent requests  
- Follow the website's terms of service
- Use reasonable check intervals (30+ seconds recommended)

## 🎯 Tips for Success

1. **Set realistic check intervals** - Don't check too frequently (30+ seconds)
2. **Monitor multiple notification channels** - Email + Discord for redundancy
3. **Test your setup** - Use the web dashboard to verify everything works
4. **Keep your API keys secure** - Never commit them to version control
5. **Monitor the logs** - Check for errors and adjust as needed

Happy Labubu hunting! 🧸✨ 