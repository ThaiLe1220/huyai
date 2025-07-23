#!/usr/bin/env python3
"""
Clean TikTok Channel Validator
Minimal output, maximum efficiency
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def setup_chrome_driver():
    """Simple Chrome driver setup with default config"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def validate_tiktok_channel_single_attempt(username, profile_url, timeout=30):
    """Single validation attempt with dual-rule checking"""

    driver = setup_chrome_driver()

    try:
        driver.get(profile_url)

        # RULE 1: Quick check for "Couldn't find this account"
        try:
            error_wait = WebDriverWait(driver, 5)
            error_container = error_wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[class*='DivErrorContainer']")
                )
            )

            error_text = error_container.text
            if "couldn't find this account" in error_text.lower():
                return {
                    "status": "❌ INVALID",
                    "message": f"Account not found: '{error_text}'",
                    "is_valid": False,
                    "rule_matched": "INVALID_RULE",
                }

        except TimeoutException:
            pass

        # RULE 2: Check for username title
        try:
            wait = WebDriverWait(driver, timeout)
            username_element = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-e2e="user-title"]')
                )
            )

            username_text = username_element.text
            return {
                "status": "✅ VALID",
                "message": f"Username title found: '{username_text}'",
                "is_valid": True,
                "rule_matched": "VALID_RULE",
            }

        except TimeoutException:
            pass

        # Neither rule matched
        return {
            "status": "❓ NO_MATCH",
            "message": "Neither valid nor invalid rule matched",
            "is_valid": None,
            "rule_matched": "NONE",
        }

    except Exception as e:
        return {
            "status": "⚠️ ERROR",
            "message": f"Error: {str(e)}",
            "is_valid": None,
            "rule_matched": "ERROR",
        }

    finally:
        driver.quit()


def validate_tiktok_channel(username, profile_url, max_attempts=3, timeout=30):
    """Validate with retry mechanism"""

    print(f"🔍 Checking: @{username}")

    for attempt in range(1, max_attempts + 1):
        attempt_start = time.time()
        result = validate_tiktok_channel_single_attempt(username, profile_url, timeout)
        attempt_time = time.time() - attempt_start

        # If we got a definitive result, return it
        if result["rule_matched"] in ["VALID_RULE", "INVALID_RULE"]:
            print(f"🎯 {result['status']} in {attempt_time:.1f}s")

            return {
                "username": username,
                "url": profile_url,
                "status": result["status"],
                "message": result["message"],
                "is_valid": result["is_valid"],
                "time_taken": attempt_time,
            }

        # If no definitive result and we have more attempts, continue
        if attempt < max_attempts:
            time.sleep(3)

    # All attempts exhausted
    print(f"❓ UNDEFINED after {max_attempts} attempts")

    return {
        "username": username,
        "url": profile_url,
        "status": "❓ UNDEFINED",
        "message": f"No definitive result after {max_attempts} attempts",
        "is_valid": None,
        "time_taken": 0,
    }


def validate_channels(channels, max_attempts=3, timeout=30):
    """Validate multiple channels with clean output"""

    print("🚀 TikTok Channel Validator")
    print("=" * 50)

    results = []
    start_time = time.time()

    for i, channel in enumerate(channels, 1):
        print(f"\n[{i}/{len(channels)}] ", end="")

        # Handle different formats
        if channel.startswith("http"):
            url = channel
            username = (
                channel.split("@")[-1].split("?")[0] if "@" in channel else "unknown"
            )
        else:
            username = channel.replace("@", "")
            url = f"https://www.tiktok.com/@{username}"

        result = validate_tiktok_channel(username, url, max_attempts, timeout)
        results.append(result)

        # Brief pause between channels
        if i < len(channels):
            time.sleep(2)

    total_time = time.time() - start_time

    # Clean Summary
    print(f"\n📋 SUMMARY:")
    print("=" * 30)

    valid = [r for r in results if r["is_valid"] is True]
    invalid = [r for r in results if r["is_valid"] is False]
    undefined = [r for r in results if r["is_valid"] is None]

    if valid:
        print(f"✅ Valid channels ({len(valid)}):")
        for r in valid:
            print(f"   @{r['username']}")

    if invalid:
        print(f"❌ Invalid channels ({len(invalid)}):")
        for r in invalid:
            print(f"   @{r['username']}")

    if undefined:
        print(f"❓ Undefined channels ({len(undefined)}):")
        for r in undefined:
            print(f"   @{r['username']}")

    print(f"\nProcessed {len(channels)} channels in {total_time:.1f}s")

    return results


def main():
    """Test with sample channels: 1 valid and 1 invalid"""
    test_channels = ["tuckerbudzyn", "mayathepolicedog"]

    results = validate_channels(test_channels, max_attempts=3, timeout=20)
    return results


if __name__ == "__main__":
    main()
