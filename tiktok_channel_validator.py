#!/usr/bin/env python3
"""
TikTok Channel Validator for CSV Files
Validates channels from CSV and outputs sorted results
"""

import time
import csv
import os
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def setup_chrome_driver():
    """Simple Chrome driver setup with default config"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
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

            # Map status to simple values for CSV
            status_map = {
                "✅ VALID": "valid",
                "❌ INVALID": "invalid",
                "❓ UNDEFINED": "undefined",
            }

            return {
                "username": username,
                "url": profile_url,
                "status": status_map.get(result["status"], "undefined"),
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
        "status": "undefined",
        "message": f"No definitive result after {max_attempts} attempts",
        "is_valid": None,
        "time_taken": 0,
    }


def read_csv(file_path):
    """Read CSV file and return list of channel dictionaries"""
    channels = []

    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found")
        return channels

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            channels.append(row)

    return channels


def read_existing_results(output_file):
    """Read existing validation results to skip already processed channels"""
    processed = {}

    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "status" in row and row["status"]:  # Only count rows with status
                    processed[row["username"]] = row

    return processed


def write_sorted_csv(channels, output_file):
    """Write channels to CSV sorted by status (valid, undefined, invalid)"""

    # Define sort order
    status_order = {"valid": 1, "undefined": 2, "invalid": 3}

    # Sort channels by status
    sorted_channels = sorted(
        channels, key=lambda x: status_order.get(x.get("status", "undefined"), 3)
    )

    if not channels:
        print("❌ No channels to write")
        return

    fieldnames = list(channels[0].keys())

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_channels)

    print(f"📄 Results saved to: {output_file}")


def validate_csv_channels(input_file, output_file, max_attempts=3, timeout=30):
    """Main function to validate channels from CSV"""

    print("🚀 TikTok Channel Validator - CSV Mode")
    print("=" * 50)

    # Read input CSV
    channels = read_csv(input_file)
    if not channels:
        return

    print(f"📂 Found {len(channels)} channels in {input_file}")

    # Read existing results to skip processed channels
    processed = read_existing_results(output_file)
    if processed:
        print(f"⏭️  Found {len(processed)} already processed channels")

    # Filter out already processed channels
    channels_to_process = []
    all_channels = []

    for channel in channels:
        username = channel["username"]

        # Add status column if not exists
        if username in processed:
            # Use existing validation result
            channel_with_status = channel.copy()
            channel_with_status["status"] = processed[username]["status"]
            all_channels.append(channel_with_status)
            print(
                f"⏭️  Skipping @{username} (already processed: {processed[username]['status']})"
            )
        else:
            # Mark for processing
            channels_to_process.append(channel)
            all_channels.append(channel)

    if not channels_to_process:
        print("✅ All channels already processed!")
        write_sorted_csv(all_channels, output_file)
        return

    print(f"🔄 Processing {len(channels_to_process)} new channels...")

    # Validate new channels
    start_time = time.time()

    for i, channel in enumerate(channels_to_process, 1):
        username = channel["username"]
        profile_url = channel["profile_url"]

        print(f"\n[{i}/{len(channels_to_process)}] ", end="")

        result = validate_tiktok_channel(username, profile_url, max_attempts, timeout)

        # Find the channel in all_channels and update status
        for j, ch in enumerate(all_channels):
            if ch["username"] == username:
                all_channels[j]["status"] = result["status"]
                break

        # Brief pause between channels
        if i < len(channels_to_process):
            time.sleep(2)

    total_time = time.time() - start_time

    # Print summary
    print(f"\n📋 VALIDATION SUMMARY:")
    print("=" * 30)

    valid = [ch for ch in all_channels if ch.get("status") == "valid"]
    invalid = [ch for ch in all_channels if ch.get("status") == "invalid"]
    undefined = [ch for ch in all_channels if ch.get("status") == "undefined"]
    no_status = [ch for ch in all_channels if not ch.get("status")]

    if valid:
        print(f"✅ Valid channels ({len(valid)}):")
        for ch in valid[:5]:  # Show first 5
            print(f"   @{ch['username']}")
        if len(valid) > 5:
            print(f"   ... and {len(valid) - 5} more")

    if undefined:
        print(f"❓ Undefined channels ({len(undefined)}):")
        for ch in undefined[:5]:  # Show first 5
            print(f"   @{ch['username']}")
        if len(undefined) > 5:
            print(f"   ... and {len(undefined) - 5} more")

    if invalid:
        print(f"❌ Invalid channels ({len(invalid)}):")
        for ch in invalid[:5]:  # Show first 5
            print(f"   @{ch['username']}")
        if len(invalid) > 5:
            print(f"   ... and {len(invalid) - 5} more")

    if no_status:
        print(f"⚠️  Channels without status ({len(no_status)})")

    print(f"\nProcessed {len(channels_to_process)} new channels in {total_time:.1f}s")

    # Write sorted results
    write_sorted_csv(all_channels, output_file)


def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(
        description="Validate TikTok channels from CSV file"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="pet_channels.csv",
        help="Input CSV file (default: pet_channels.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="validated_channels.csv",
        help="Output CSV file (default: validated_channels.csv)",
    )
    parser.add_argument(
        "--attempts",
        "-a",
        type=int,
        default=3,
        help="Max validation attempts per channel (default: 3)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=30,
        help="Timeout per attempt in seconds (default: 30)",
    )

    args = parser.parse_args()

    validate_csv_channels(args.input, args.output, args.attempts, args.timeout)


if __name__ == "__main__":
    main()
