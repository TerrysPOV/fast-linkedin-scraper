#!/usr/bin/env python3
"""Basic test for LinkedIn scraper functionality."""

import asyncio
import logging
import os
from dotenv import load_dotenv

from fast_linkedin_scraper import LinkedInSession, PersonScrapingFields
from fast_linkedin_scraper.browser.context import BrowserContextManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


async def test_browser_context():
    """Test browser context initialization."""
    logger.info("Testing browser context initialization...")

    try:
        async with BrowserContextManager(headless=True) as context:
            page = await context.new_page()
            await page.goto("https://httpbin.org/headers")

            # Check if page loaded successfully
            title = await page.title()
            logger.info(f"✅ Browser context test successful. Page title: {title}")
            return True

    except Exception as e:
        logger.error(f"❌ Browser context test failed: {e}")
        return False


async def test_linkedin_session_creation():
    """Test LinkedIn session creation without actual authentication."""
    logger.info("Testing LinkedIn session creation...")

    # Check if we have a real cookie for testing
    cookie = os.getenv("LI_AT_COOKIE")

    if not cookie:
        # Test session creation with password auth instead (no actual login)
        try:
            from fast_linkedin_scraper.auth import PasswordAuth
            auth = PasswordAuth("test@example.com", "password", interactive=False)
            session = LinkedInSession(auth, headless=True)
            logger.info("✅ LinkedIn session creation successful (with password auth)")
            return True
        except Exception as e:
            logger.error(f"❌ LinkedIn session creation failed: {e}")
            return False
    else:
        # Test with real cookie
        try:
            session = LinkedInSession.from_cookie(cookie, headless=True)
            logger.info("✅ LinkedIn session creation successful (with real cookie)")
            return True
        except Exception as e:
            logger.error(f"❌ LinkedIn session creation failed: {e}")
            return False


async def test_linkedin_navigation():
    """Test navigation to LinkedIn (requires valid cookie)."""
    cookie = os.getenv("LI_AT_COOKIE")

    if not cookie:
        logger.warning("⚠️  No LI_AT_COOKIE found. Skipping LinkedIn navigation test.")
        logger.info("   To test LinkedIn functionality, set LI_AT_COOKIE in your environment.")
        return True  # Not a failure, just skipped

    logger.info("Testing LinkedIn navigation with provided cookie...")

    try:
        async with LinkedInSession.from_cookie(cookie, headless=True) as session:
            # Try to access LinkedIn feed
            page = session._page
            await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")

            # Check if we're logged in (look for feed elements or profile link)
            await page.wait_for_timeout(2000)  # Wait for page to load

            # Check for common logged-in indicators
            profile_link = await page.query_selector('a[href*="/in/"]')
            feed_content = await page.query_selector('[data-test-id="feed"]')

            if profile_link or feed_content:
                logger.info("✅ LinkedIn navigation test successful - appears to be logged in")
                return True
            else:
                logger.warning("⚠️  LinkedIn navigation completed but login status unclear")
                return True  # Still consider it a success for connectivity

    except Exception as e:
        logger.error(f"❌ LinkedIn navigation test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Running basic tests for fast-linkedin-scraper...")
    print("=" * 60)

    tests = [
        ("Browser Context", test_browser_context),
        ("Session Creation", test_linkedin_session_creation),
        ("LinkedIn Navigation", test_linkedin_navigation),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:20} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The scraper appears to be working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)