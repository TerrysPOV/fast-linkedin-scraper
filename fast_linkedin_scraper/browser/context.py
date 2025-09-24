"""Simple browser management for LinkedIn scraping."""

import logging
import os
from typing import Optional

from playwright.async_api import BrowserContext, async_playwright

from ..config import BrowserConfig
from ..exceptions import DriverInitializationError

logger = logging.getLogger(__name__)


class BrowserContextManager:
    """Context manager for browser contexts with automatic cleanup."""

    def __init__(self, headless: bool = True, channel: Optional[str] = None):
        self.headless = headless
        self.channel = channel
        self.playwright_context = None
        self.browser = None

    async def __aenter__(self) -> BrowserContext:
        """Create and return browser context with enhanced configuration."""
        try:
            self.playwright_context = async_playwright()
            playwright = await self.playwright_context.__aenter__()

            # Determine Chrome arguments based on headless mode
            if self.headless:
                chrome_args = BrowserConfig.get_chrome_args_for_headless()
            else:
                chrome_args = BrowserConfig.get_chrome_args_for_visible()

            # Attempt multiple Chrome installation methods
            browser_options = {
                "headless": self.headless,
                "args": chrome_args,
            }

            # Try different Chrome channels/installations
            channels_to_try = []
            if self.channel:
                channels_to_try.append(self.channel)

            # Add common Chrome installation channels
            channels_to_try.extend([
                "chrome",  # Standard Chrome installation
                "chrome-stable",  # Linux Chrome stable
                "chrome-beta",  # Chrome beta
                None,  # Use bundled Chromium
            ])

            browser = None
            last_error = None

            for channel in channels_to_try:
                try:
                    if channel:
                        browser_options["channel"] = channel
                        logger.info(f"Attempting to launch Chrome with channel: {channel}")
                    else:
                        browser_options.pop("channel", None)
                        logger.info("Attempting to launch bundled Chromium")

                    browser = await playwright.chromium.launch(**browser_options)
                    logger.info(f"Successfully launched browser with channel: {channel or 'bundled-chromium'}")
                    break

                except Exception as e:
                    last_error = e
                    logger.warning(f"Failed to launch with channel '{channel}': {e}")
                    continue

            if browser is None:
                raise DriverInitializationError(
                    f"Failed to initialize browser after trying all available options. "
                    f"Last error: {last_error}. "
                    f"Please ensure Chrome is installed or run 'playwright install chromium'."
                )

            self.browser = browser

            # Create context with enhanced configuration
            context = await browser.new_context(
                user_agent=BrowserConfig.USER_AGENT,
                viewport=BrowserConfig.VIEWPORT,
                # Enhanced context options for anti-detection
                ignore_https_errors=True,
                java_script_enabled=True,
                accept_downloads=False,
                bypass_csp=True,
                # Locale and timezone settings
                locale="en-US",
                timezone_id="America/New_York",
            )

            # Set timeout and other configurations
            context.set_default_timeout(BrowserConfig.TIMEOUT)
            context.set_default_navigation_timeout(BrowserConfig.TIMEOUT)

            # Add additional stealth measures
            await context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });

                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)

            return context

        except Exception as e:
            # Clean up on failure
            if self.browser:
                await self.browser.close()
            if self.playwright_context:
                await self.playwright_context.__aexit__(None, None, None)

            if isinstance(e, DriverInitializationError):
                raise
            else:
                raise DriverInitializationError(f"Browser initialization failed: {e}") from e

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensure browser and playwright are properly closed."""
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")

        try:
            if self.playwright_context:
                await self.playwright_context.__aexit__(exc_type, exc_val, exc_tb)
        except Exception as e:
            logger.warning(f"Error closing playwright context: {e}")

    @staticmethod
    def check_chrome_installation() -> dict:
        """Check for Chrome installation and return status information."""
        status = {
            "chrome_installed": False,
            "chromium_available": False,
            "chrome_paths": [],
            "recommendations": []
        }

        # Common Chrome installation paths
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
            "/usr/bin/google-chrome",  # Linux
            "/usr/bin/google-chrome-stable",  # Linux
            "/usr/bin/chromium-browser",  # Linux Chromium
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Windows
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",  # Windows 32-bit
        ]

        for path in chrome_paths:
            if os.path.exists(path):
                status["chrome_installed"] = True
                status["chrome_paths"].append(path)

        # Check if Playwright's Chromium is available
        try:
            import playwright
            status["chromium_available"] = True
        except ImportError:
            status["recommendations"].append("Install Playwright: pip install playwright")
            status["recommendations"].append("Install browsers: playwright install chromium")

        if not status["chrome_installed"] and not status["chromium_available"]:
            status["recommendations"].extend([
                "Install Google Chrome from https://www.google.com/chrome/",
                "Or use Playwright's Chromium: playwright install chromium"
            ])

        return status
