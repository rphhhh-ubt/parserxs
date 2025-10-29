# Aiogram Bot with Playwright

A Telegram bot built with aiogram that integrates Playwright for web automation and screenshot capabilities.

## Features

- Take screenshots of websites using Playwright's Chromium browser
- Health check command to verify Playwright functionality
- Dockerized for easy deployment
- Configurable logging and timeout settings
- Headless browser operation optimized for containers

## Prerequisites

- Python 3.11+
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- Docker and Docker Compose (for containerized deployment)

## Setup Instructions

### Option 1: Local Development (without Docker)

#### 1. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Install Playwright Browsers

Playwright requires browser binaries to be installed:

```bash
playwright install chromium
# For full system dependencies (Linux):
playwright install --with-deps chromium
```

#### 4. Configure Environment Variables

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Edit `.env` and set your bot token:

```env
BOT_TOKEN=your_actual_bot_token_here
LOG_LEVEL=INFO
PLAYWRIGHT_TIMEOUT=30000
LOCALE=en-US
```

#### 5. Run the Bot

```bash
python bot.py
```

### Option 2: Docker Deployment (Recommended)

#### 1. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your bot token and preferences.

#### 2. Build Docker Image

```bash
docker build -t aiogram-playwright-bot .
```

#### 3. Run with Docker

```bash
docker run -d \
  --name aiogram-bot \
  --env-file .env \
  --restart unless-stopped \
  aiogram-playwright-bot
```

#### 4. Run with Docker Compose (Recommended)

```bash
docker-compose up -d
```

To view logs:

```bash
docker-compose logs -f
```

To stop:

```bash
docker-compose down
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | - | Yes |
| `LOG_LEVEL` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO | No |
| `PLAYWRIGHT_TIMEOUT` | Page load timeout in milliseconds | 30000 | No |
| `LOCALE` | Browser locale (e.g., en-US, de-DE, fr-FR) | en-US | No |

### Configuring Logging Level

Set the `LOG_LEVEL` environment variable to control verbosity:

- **DEBUG**: Detailed information, typically for diagnosing problems
- **INFO**: Confirmation that things are working as expected (default)
- **WARNING**: Indication that something unexpected happened
- **ERROR**: More serious problem, the software has not been able to perform a function
- **CRITICAL**: Serious error, the program may be unable to continue running

Example:
```bash
LOG_LEVEL=DEBUG python bot.py
```

## Available Commands

- `/start` - Display welcome message and available commands
- `/health` - Check if the bot and Playwright are working correctly
- `/screenshot <url>` - Take a screenshot of the specified URL

## Timeout and Region Limitations

### Timeout Configuration

The `PLAYWRIGHT_TIMEOUT` environment variable controls how long Playwright waits for pages to load before timing out. The default is 30 seconds (30000ms).

**Considerations:**
- Slower websites may require longer timeouts (e.g., 60000ms)
- Shorter timeouts (e.g., 15000ms) can fail on slow networks
- Balance between responsiveness and reliability

**Example:**
```env
PLAYWRIGHT_TIMEOUT=60000  # 60 seconds
```

### Region and Locale

The `LOCALE` variable sets the browser's locale, which affects:
- Language displayed on websites
- Date/time formatting
- Regional content availability

Some websites may restrict access based on the bot's IP location or locale settings. If you encounter region-specific issues:

1. Check if the website has geo-restrictions
2. Verify the locale matches your needs
3. Consider using a VPN or proxy if necessary (not included)

**Common locales:**
- `en-US` - English (United States)
- `en-GB` - English (United Kingdom)
- `de-DE` - German (Germany)
- `fr-FR` - French (France)
- `es-ES` - Spanish (Spain)
- `ru-RU` - Russian (Russia)

## Troubleshooting

### Playwright in Headless Environments

Running Playwright in Docker or headless Linux environments can present challenges. Here are common issues and solutions:

#### 1. Browser Launch Fails

**Symptoms:**
- Error: "Executable doesn't exist"
- Browser fails to launch

**Solutions:**
```bash
# Reinstall Playwright browsers
playwright install --with-deps chromium

# In Docker, ensure the Dockerfile includes system dependencies
# (already included in the provided Dockerfile)
```

#### 2. Shared Memory Issues

**Symptoms:**
- Error: "Failed to launch chromium"
- "/dev/shm" related errors

**Solutions:**

Add to Docker run command:
```bash
docker run --shm-size=2gb ...
```

Or in docker-compose.yml:
```yaml
services:
  bot:
    shm_size: '2gb'
```

#### 3. Permission Errors

**Symptoms:**
- Permission denied errors
- Browser crashes

**Solutions:**

The Dockerfile runs as a non-root user by default. If you encounter issues:
```bash
# Check file permissions
docker exec -it aiogram-bot ls -la /app
```

#### 4. Timeout Errors

**Symptoms:**
- "Timeout 30000ms exceeded"
- Slow page loads

**Solutions:**
1. Increase timeout: `PLAYWRIGHT_TIMEOUT=60000`
2. Wait for different load state:
   ```python
   await page.goto(url, wait_until="domcontentloaded")
   ```
3. Check network connectivity in container

#### 5. Font Rendering Issues

**Symptoms:**
- Screenshots show boxes instead of text
- Missing characters

**Solutions:**

The Dockerfile includes font packages, but for additional fonts:
```dockerfile
RUN apt-get install -y fonts-noto fonts-noto-cjk
```

#### 6. Memory Issues

**Symptoms:**
- Container crashes
- Out of memory errors

**Solutions:**
```bash
# Limit memory in docker-compose.yml
services:
  bot:
    mem_limit: 1g
    memswap_limit: 1g
```

#### 7. Debugging Playwright Issues

Enable verbose logging:
```env
LOG_LEVEL=DEBUG
```

Test Playwright manually in container:
```bash
docker exec -it aiogram-bot python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    print('Browser launched successfully!')
    browser.close()
"
```

#### 8. Network Issues

**Symptoms:**
- Cannot reach certain websites
- DNS resolution failures

**Solutions:**
```bash
# Test DNS resolution
docker exec -it aiogram-bot ping -c 3 google.com

# Add DNS servers to docker-compose.yml
services:
  bot:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

## Development

### Project Structure

```
.
├── bot.py                 # Main bot application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── .env.example          # Example environment variables
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

### Adding New Features

1. Install development environment as described above
2. Modify `bot.py` with new commands or functionality
3. Test locally before building Docker image
4. Update documentation as needed

### Testing Changes with Docker

For rapid development iteration:

```bash
# Use volume mounting (already in docker-compose.yml)
docker-compose up

# After code changes, restart:
docker-compose restart
```

## Security Notes

- Never commit `.env` file to version control
- Keep your bot token secret
- The Docker container runs as a non-root user for security
- Review and limit bot permissions as needed

## License

This project is provided as-is for educational and development purposes.

## Support

For issues related to:
- **aiogram**: [aiogram documentation](https://docs.aiogram.dev/)
- **Playwright**: [Playwright documentation](https://playwright.dev/python/)
- **Docker**: [Docker documentation](https://docs.docker.com/)
