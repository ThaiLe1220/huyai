from openai import OpenAI
import csv
import re
import os
import argparse
from datetime import datetime

client = OpenAI()


def find_pet_channels(search_keywords="", target_count=20, country="US"):
    """Find popular TikTok pet and animal channels with specific keywords and country using web search"""

    # Build user prompt with keywords and target count
    base_prompt = f"Find popular TikTok channels that focus on pet and animal content. Find exactly {target_count} unique channels."

    if search_keywords:
        keyword_prompt = (
            f" Focus specifically on channels related to: {search_keywords}."
        )
        user_prompt = (
            base_prompt
            + keyword_prompt
            + " Provide TikTok usernames only (@username format), one per line."
        )
    else:
        user_prompt = (
            base_prompt
            + " Provide TikTok usernames only (@username format), one per line."
        )

    # Updated system prompt to emphasize country-specific search
    system_prompt = f"""You are a TikTok channel finder focused on pet and animal content creators from {country}. Your job is to find and list popular TikTok channels that focus on pets, animals, dogs, cats, and similar content, specifically targeting creators from {country}.

REQUIREMENTS:
- Only provide TikTok usernames in this format: @username
- Focus on channels that primarily post pet/animal content
- Find exactly {target_count} unique channels
- Prefer popular/trending creators with high followers from {country}
- Include variety: dogs, cats, exotic pets, pet training, funny pets, etc.
- Use web search to find current, active channels
- No explanations needed - just provide the usernames, one per line"""

    # Use the new responses.create API with web search
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {
                    "type": "approximate",
                    "country": country,
                },
                "search_context_size": "medium",
            }
        ],
        temperature=1,
        max_output_tokens=10000,
        top_p=1,
        store=False,
    )

    # Updated response parsing for the new API format
    # The new API returns the content differently
    return response.content[0].text


def extract_usernames(response_text):
    """Extract usernames from the response and clean them"""
    # Find all @username patterns
    usernames = re.findall(r"@([a-zA-Z0-9._]+)", response_text)

    # Remove duplicates while preserving order
    unique_usernames = []
    seen = set()
    for username in usernames:
        if username not in seen:
            unique_usernames.append(username)
            seen.add(username)

    return unique_usernames


def load_existing_channels(csv_filename="pet_channels.csv"):
    """Load existing channels from CSV"""
    existing_channels = {}

    if os.path.exists(csv_filename):
        try:
            with open(csv_filename, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_channels[row["username"].lower()] = row
        except Exception as e:
            print(f"⚠️  Warning: Could not read existing CSV: {e}")

    return existing_channels


def update_channel_data(existing_row, new_keywords, new_country):
    """Update existing channel with new keywords and country"""
    # Combine keywords
    existing_keywords = existing_row.get("keywords", "")
    if existing_keywords and new_keywords:
        combined_keywords = f"{existing_keywords}, {new_keywords}"
    else:
        combined_keywords = new_keywords or existing_keywords

    # Combine countries
    existing_countries = existing_row.get("country", "")
    if existing_countries and new_country not in existing_countries:
        combined_countries = f"{existing_countries}, {new_country}"
    else:
        combined_countries = new_country if new_country else existing_countries

    # Update the row
    existing_row["keywords"] = combined_keywords
    existing_row["country"] = combined_countries
    existing_row["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return existing_row


def save_channels_to_csv(
    usernames, csv_filename="pet_channels.csv", search_keywords="", country="US"
):
    """Save channels to CSV, updating existing records instead of duplicating"""

    # Load existing channels
    existing_channels = load_existing_channels(csv_filename)

    # Get current timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate search run ID
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M')}"

    # Use provided keywords or default
    keywords_to_save = search_keywords if search_keywords else "general_search"

    new_channels = []
    updated_channels = []

    for username in usernames:
        if username.lower() in existing_channels:
            # Update existing channel
            updated_row = update_channel_data(
                existing_channels[username.lower()], keywords_to_save, country
            )
            updated_channels.append(updated_row)
        else:
            # Add new channel
            new_channels.append(
                {
                    "username": username,
                    "profile_url": f"https://www.tiktok.com/@{username}",
                    "first_found": current_time,
                    "last_updated": current_time,
                    "search_run": run_id,
                    "keywords": keywords_to_save,
                    "country": country,
                }
            )

    # Write all data back to CSV
    all_channels = list(existing_channels.values()) + new_channels

    # Update the existing channels with new data
    for updated in updated_channels:
        for i, channel in enumerate(all_channels):
            if channel["username"].lower() == updated["username"].lower():
                all_channels[i] = updated
                break

    # Write to CSV
    if all_channels:
        with open(csv_filename, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "username",
                "profile_url",
                "first_found",
                "last_updated",
                "search_run",
                "keywords",
                "country",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write data
            for channel in all_channels:
                writer.writerow(channel)

        print(f"✅ Added {len(new_channels)} new channels")
        print(f"🔄 Updated {len(updated_channels)} existing channels")
        print(f"📊 Total channels in database: {len(all_channels)}")

    print(f"🏷️  Keywords: {keywords_to_save}")
    print(f"🌍 Country: {country}")
    print(f"🆔 Search run: {run_id}")

    return len(new_channels), len(updated_channels)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="TikTok Pet Channel Finder")
    parser.add_argument(
        "--target",
        "-t",
        type=int,
        default=20,
        help="Target number of channels to find (default: 20)",
    )
    parser.add_argument(
        "--keywords",
        "-k",
        type=str,
        default="",
        help="Search keywords (comma-separated)",
    )
    parser.add_argument(
        "--country",
        "-c",
        type=str,
        choices=["US", "IN", "ID", "BD", "VN"],
        default="US",
        help="Country for search targeting (default: US)",
    )

    args = parser.parse_args()

    print("🔍 TikTok Pet Channel Finder")
    print("=" * 40)
    print(f"🎯 Target: {args.target} channels")
    print(f"🌍 Country: {args.country}")
    if args.keywords:
        print(f"🏷️  Keywords: {args.keywords}")

    if not args.keywords:
        print("\n❌ No keywords provided. Use --keywords to specify search terms.")
        exit(1)

    print(f"\n🔍 Searching for {args.target} pet TikTok channels...")

    # Get channels from OpenAI
    response = find_pet_channels(args.keywords, args.target, args.country)
    print("\n📄 Raw response:")
    print(response)
    print("\n" + "=" * 50 + "\n")

    # Extract and clean usernames
    usernames = extract_usernames(response)
    print(f"🔍 Found {len(usernames)} channels in response:")

    # Display found channels
    for i, username in enumerate(usernames, 1):
        print(f"{i:2d}. @{username}")

    # Save to CSV
    new_count, updated_count = save_channels_to_csv(
        usernames, search_keywords=args.keywords, country=args.country
    )

    print(f"\n🎉 Complete! Processed {len(usernames)} channels")
    print(f"📄 Data saved to: pet_channels.csv")
