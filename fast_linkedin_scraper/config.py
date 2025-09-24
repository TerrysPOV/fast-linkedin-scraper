"""Configuration settings for the LinkedIn scraper."""

from enum import Flag, auto
from playwright.async_api import ViewportSize


class BrowserConfig:
    """Browser configuration settings."""

    # Modern user agent that gets updated regularly
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    VIEWPORT: ViewportSize = {"width": 1920, "height": 1080}
    TIMEOUT = 15000  # timeout in ms

    # Enhanced Chrome arguments for better compatibility and anti-detection
    CHROME_ARGS = [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        # Additional anti-detection measures
        "--exclude-switches=enable-automation",
        "--disable-extensions-file-access-check",
        "--disable-extensions-http-throttling",
        "--disable-component-extensions-with-background-pages",
        "--disable-default-apps",
        "--disable-sync",
        "--no-pings",
        "--disable-background-networking",
        # Performance and stability improvements
        "--disable-ipc-flooding-protection",
        "--disable-hang-monitor",
        "--disable-prompt-on-repost",
        "--disable-client-side-phishing-detection",
        "--disable-component-update",
        "--disable-domain-reliability",
        # Memory and resource optimization
        "--memory-pressure-off",
        "--max_old_space_size=4096",
        "--single-process"  # Use with caution, may cause issues on some systems
    ]

    @classmethod
    def get_chrome_args_for_headless(cls) -> list[str]:
        """Get Chrome arguments optimized for headless mode."""
        headless_args = cls.CHROME_ARGS.copy()
        headless_args.extend([
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-software-rasterizer",
            "--run-all-compositor-stages-before-draw",
            "--disable-threaded-animation",
            "--disable-threaded-scrolling",
            "--disable-checker-imaging",
            "--disable-new-content-rendering-timeout",
            "--disable-image-animation-resync"
        ])
        return headless_args

    @classmethod
    def get_chrome_args_for_visible(cls) -> list[str]:
        """Get Chrome arguments optimized for visible mode."""
        visible_args = [arg for arg in cls.CHROME_ARGS if arg != "--single-process"]
        return visible_args


class PersonScrapingFields(Flag):
    """Fields that can be scraped from LinkedIn person profiles.

    Each field corresponds to specific profile sections and navigation requirements:

    - BASIC_INFO: Name, headline, location, about (scraped from main page, ~2s)
    - EXPERIENCE: Work history (navigates to /details/experience, ~5s)
    - EDUCATION: Education history (navigates to /details/education, ~5s)
    - INTERESTS: Following/interests (navigates to /details/interests, ~5s)
    - ACCOMPLISHMENTS: Honors and languages (multiple navigations, ~6s)
    - CONTACTS: Contact info and connections (modal + navigation, ~8s)
    """

    BASIC_INFO = auto()  # Name, headline, location, about
    EXPERIENCE = auto()  # Work history and employment details
    EDUCATION = auto()  # Educational background and degrees
    INTERESTS = auto()  # Following companies/people and interests
    ACCOMPLISHMENTS = auto()  # Honors, awards, and languages
    CONTACTS = auto()  # Contact information and connections

    # Presets for common use cases
    MINIMAL = BASIC_INFO  # Fastest: basic info only (~2s)
    CAREER = BASIC_INFO | EXPERIENCE | EDUCATION  # Career-focused (~12s)
    ALL = (
        BASIC_INFO | EXPERIENCE | EDUCATION | INTERESTS | ACCOMPLISHMENTS | CONTACTS
    )  # Complete profile (~30s)
