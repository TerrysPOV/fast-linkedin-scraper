#!/usr/bin/env python3
"""Chrome diagnostics and setup utility for fast-linkedin-scraper."""

import asyncio
import logging
import sys
from typing import Dict, Any

from fast_linkedin_scraper.browser.context import BrowserContextManager
from fast_linkedin_scraper.exceptions import DriverInitializationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def test_browser_initialization() -> Dict[str, Any]:
    """Test browser initialization with different configurations."""
    results = {
        "chrome_status": BrowserContextManager.check_chrome_installation(),
        "initialization_tests": []
    }

    test_configs = [
        {"name": "Chrome Stable", "headless": True, "channel": "chrome"},
        {"name": "Chrome Beta", "headless": True, "channel": "chrome-beta"},
        {"name": "Bundled Chromium", "headless": True, "channel": None},
        {"name": "Chrome Visible Mode", "headless": False, "channel": "chrome"},
    ]

    for config in test_configs:
        logger.info(f"Testing {config['name']}...")
        test_result = {
            "name": config["name"],
            "success": False,
            "error": None,
            "config": config
        }

        try:
            browser_manager = BrowserContextManager(
                headless=config["headless"],
                channel=config["channel"]
            )

            async with browser_manager as context:
                # Simple page navigation test
                page = await context.new_page()
                await page.goto("https://httpbin.org/user-agent")
                user_agent_info = await page.text_content("body")

                test_result["success"] = True
                test_result["user_agent"] = user_agent_info
                logger.info(f"✅ {config['name']} - Success")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ {config['name']} - Failed: {e}")

        results["initialization_tests"].append(test_result)

    return results


def print_diagnostics_report(results: Dict[str, Any]) -> None:
    """Print a comprehensive diagnostics report."""
    print("\n" + "="*80)
    print("CHROME DIAGNOSTICS REPORT")
    print("="*80)

    # Chrome Installation Status
    print("\n📋 CHROME INSTALLATION STATUS:")
    status = results["chrome_status"]
    print(f"   Chrome Installed: {'✅' if status['chrome_installed'] else '❌'}")
    print(f"   Chromium Available: {'✅' if status['chromium_available'] else '❌'}")

    if status["chrome_paths"]:
        print("   Chrome Paths Found:")
        for path in status["chrome_paths"]:
            print(f"     - {path}")

    if status["recommendations"]:
        print("\n   Recommendations:")
        for rec in status["recommendations"]:
            print(f"     - {rec}")

    # Initialization Tests
    print("\n🧪 BROWSER INITIALIZATION TESTS:")
    successful_configs = []
    failed_configs = []

    for test in results["initialization_tests"]:
        if test["success"]:
            successful_configs.append(test)
            print(f"   ✅ {test['name']}")
        else:
            failed_configs.append(test)
            print(f"   ❌ {test['name']}: {test['error']}")

    # Recommendations
    print("\n💡 RECOMMENDATIONS:")

    if successful_configs:
        print("   Working configurations found:")
        for config in successful_configs:
            channel = config["config"]["channel"] or "bundled-chromium"
            headless = "headless" if config["config"]["headless"] else "visible"
            print(f"     - Use channel '{channel}' in {headless} mode")

    if failed_configs and not successful_configs:
        print("   ⚠️  No working configurations found. Try these steps:")
        print("     1. Install Google Chrome: https://www.google.com/chrome/")
        print("     2. Reinstall Playwright browsers: playwright install chromium")
        print("     3. Check system permissions for browser automation")
        print("     4. Try running with --no-sandbox flag")

    if any(test["success"] for test in results["initialization_tests"]):
        print("\n✅ DIAGNOSIS: Browser automation is working!")
        print("   You can use the fast-linkedin-scraper with confidence.")
    else:
        print("\n❌ DIAGNOSIS: Browser automation issues detected!")
        print("   Please follow the recommendations above before using the scraper.")


async def main():
    """Run Chrome diagnostics."""
    print("Starting Chrome diagnostics for fast-linkedin-scraper...")
    print("This will test various browser configurations and provide recommendations.")

    try:
        results = await test_browser_initialization()
        print_diagnostics_report(results)

        # Exit code based on results
        if any(test["success"] for test in results["initialization_tests"]):
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # No working configurations found

    except KeyboardInterrupt:
        print("\n\nDiagnostics interrupted by user.")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())