#!/usr/bin/env python3
"""
Bitwarden API Key Manager for OpenDiscourse MCP
Fetches API keys from Bitwarden and updates environment configuration
"""

import os
import json
import subprocess
import sys
from pathlib import Path

# Bitwarden configuration
BITWARDEN_CONFIG = {
    "server": None,  # Use default Bitwarden server
    "email": None,  # Will be set via environment or prompt
    "password": None,  # Will be set via environment or prompt
    "items": {
        "govinfo_api_key": {"name": "GovInfo API Key", "field_name": "api_key"},
        "congress_api_key": {"name": "Congress.gov API Key", "field_name": "api_key"},
    },
}


def check_bitwarden_cli():
    """Check if Bitwarden CLI is installed"""
    try:
        result = subprocess.run(["bw", "--version"], capture_output=True, text=True)
        print(f"✅ Bitwarden CLI found: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Bitwarden CLI not found")
        print("Please install Bitwarden CLI:")
        print("  npm install -g @bitwarden/cli")
        print("  or visit: https://bitwarden.com/help/article/cli/")
        return False


def unlock_bitwarden():
    """Unlock Bitwarden vault"""
    email = os.getenv("BITWARDEN_EMAIL")
    password = os.getenv("BITWARDEN_PASSWORD")

    if not email:
        email = input("Enter Bitwarden email: ")
    if not password:
        password = input("Enter Bitwarden password: ")

    try:
        # Check if already unlocked
        result = subprocess.run(["bw", "status"], capture_output=True, text=True)
        if "unlocked" in result.stdout.lower():
            print("✅ Bitwarden already unlocked")
            return True

        # Unlock vault
        print("🔓 Unlocking Bitwarden vault...")
        subprocess.run(
            ["bw", "unlock", "--passwordenv", "BITWARDEN_PASSWORD"],
            env={**os.environ, "BITWARDEN_PASSWORD": password},
        )

        # Verify unlock
        result = subprocess.run(["bw", "status"], capture_output=True, text=True)
        if "unlocked" in result.stdout.lower():
            print("✅ Bitwarden vault unlocked successfully")
            return True
        else:
            print("❌ Failed to unlock Bitwarden vault")
            return False
    except Exception as e:
        print(f"❌ Error unlocking Bitwarden: {e}")
        return False


def search_api_key(item_name, field_name):
    """Search for API key in Bitwarden"""
    try:
        # Search by item name
        result = subprocess.run(
            ["bw", "list", "items", "--search", item_name],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            items = json.loads(result.stdout)
            for item in items:
                # Check if this is the right item
                if item_name.lower() in item.get("name", "").lower():
                    # Get item details
                    item_id = item["id"]
                    detail_result = subprocess.run(
                        ["bw", "get", "item", item_id], capture_output=True, text=True
                    )

                    if detail_result.returncode == 0:
                        item_detail = json.loads(detail_result.stdout)

                        # Look for API key in fields
                        for field in item_detail.get("fields", []):
                            if field.get("name", "").lower() == field_name.lower():
                                return field.get("value", "")

                        # Check notes for API key
                        notes = item_detail.get("notes", "")
                        if any(
                            keyword.lower() in notes.lower()
                            for keyword in ["api", "key", "token"]
                        ):
                            # Try to extract key from notes
                            lines = notes.split("\n")
                            for line in lines:
                                if any(
                                    keyword in line.lower()
                                    for keyword in ["api", "key", "token"]
                                ):
                                    # Extract key value
                                    if ":" in line:
                                        return line.split(":", 1)[1].strip()
                                    return line.strip()

                        # Check name field
                        name = item_detail.get("name", "")
                        if any(
                            keyword.lower() in name.lower()
                            for keyword in ["api", "key", "token"]
                        ):
                            return name
    except json.JSONDecodeError as e:
        print(f"Error parsing search results: {e}")
    except Exception as e:
        print(f"Error searching for {item_name}: {e}")

    return None


def fetch_all_api_keys():
    """Fetch all required API keys from Bitwarden"""
    api_keys = {}

    if not unlock_bitwarden():
        return None

    print("🔍 Fetching API keys from Bitwarden...")

    for key_type, config in BITWARDEN_CONFIG["items"].items():
        print(f"  Searching for {config['name']}...")

        api_key = search_api_key(config["name"], config["field_name"])

        if api_key:
            api_keys[key_type] = api_key
            print(f"  ✅ Found {config['name']}")
        else:
            print(f"  ❌ {config['name']} not found")
            # Try manual search
            manual_key = input(
                f"  Enter {config['name']} manually (or press Enter to skip): "
            ).strip()
            if manual_key:
                api_keys[key_type] = manual_key

    return api_keys


def update_env_file(api_keys):
    """Update .env file with API keys"""
    env_file = Path(".env")
    env_content = []

    # Read existing .env file
    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.readlines()

    # Update or add API keys
    key_updated = False
    for i, line in enumerate(env_content):
        line = line.strip()
        if line.startswith("GOVINFO_API_KEY="):
            env_content[i] = f"GOVINFO_API_KEY={api_keys.get('govinfo_api_key', '')}\n"
            key_updated = True
        elif line.startswith("CONGRESS_API_KEY="):
            env_content[i] = (
                f"CONGRESS_API_KEY={api_keys.get('congress_api_key', '')}\n"
            )
            key_updated = True

    # Add new keys if not found
    if not key_updated:
        env_content.append(f"GOVINFO_API_KEY={api_keys.get('govinfo_api_key', '')}\n")
        env_content.append(f"CONGRESS_API_KEY={api_keys.get('congress_api_key', '')}\n")

    # Write updated .env file
    with open(env_file, "w") as f:
        f.writelines(env_content)

    print("✅ .env file updated successfully")


def update_database_config(api_keys):
    """Update database configuration with API keys"""
    try:
        # Try to import psycopg2
        try:
            import psycopg2
        except ImportError:
            print("📦 Installing psycopg2...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--user", "psycopg2-binary"]
            )
            import psycopg2

        # Test database connection
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="opendiscourse",
            user="opendiscourse",
            password="opendiscourse123",
        )
        cursor = conn.cursor()

        # Test connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {version}")

        for service, key_value in api_keys.items():
            if key_value:
                service_name = service.replace("_api_key", "").upper()
                cursor.execute(
                    """
                    INSERT INTO api_keys (service, key_value, is_active)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (service) 
                    DO UPDATE SET 
                        key_value = EXCLUDED.key_value,
                        updated_at = CURRENT_TIMESTAMP,
                        is_active = TRUE
                """,
                    (service_name, key_value, True),
                )

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ API keys stored in database successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to update database: {e}")
        return False


def main():
    """Main function"""
    print("🔐 OpenDiscourse MCP - Bitwarden API Key Manager")
    print("=" * 50)

    # Check Bitwarden CLI
    if not check_bitwarden_cli():
        sys.exit(1)

    # Fetch API keys
    api_keys = fetch_all_api_keys()

    if not api_keys:
        print("❌ No API keys found. Please add them to Bitwarden first.")
        sys.exit(1)

    # Display found keys
    print("\n📋 Found API Keys:")
    for key_type, key_value in api_keys.items():
        if key_value:
            masked_key = key_value[:8] + "..." if len(key_value) > 8 else "***"
            print(f"  {key_type}: {masked_key}")

    # Update .env file
    update_env_file(api_keys)

    # Update database with API keys
    update_database_config(api_keys)

    print("\n✅ Setup complete! Your API keys have been:")
    print("  • Stored in .env file")
    print("  • Stored in database")
    print("  • Ready for MCP server use")


if __name__ == "__main__":
    main()
