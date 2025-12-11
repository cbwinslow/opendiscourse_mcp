#!/usr/bin/env python3.10
"""
Simple utility to find the upper limit for congress numbers.

This script provides multiple methods to determine the highest available congress number:
1. From configured available sessions (hardcoded)
2. From actual data directory structure
3. From current year estimation
"""

from pathlib import Path
from datetime import datetime

# Hardcoded available sessions (same as enums)
AVAILABLE_SESSIONS = list(range(113, 124))  # 113th to 123rd Congress

def get_upper_limit_from_config() -> int:
    """Get upper limit from configured available sessions."""
    return max(AVAILABLE_SESSIONS) if AVAILABLE_SESSIONS else 0

def get_upper_limit_from_data(data_dir: Path = None) -> int:
    """Find upper limit from actual data directory structure."""
    if data_dir is None:
        data_dir = Path("govinfo_data")

    if not data_dir.exists():
        print(f"Data directory {data_dir} does not exist")
        return 0

    congress_dirs = []
    for item in data_dir.iterdir():
        if item.is_dir() and item.name.isdigit():
            try:
                congress_num = int(item.name)
                congress_dirs.append(congress_num)
            except ValueError:
                continue

    if not congress_dirs:
        print("No congress directories found")
        return 0

    return max(congress_dirs)

def estimate_upper_limit_from_current_year() -> int:
    """Estimate upper limit based on current year."""
    current_year = datetime.now().year
    # Congress sessions start in odd years and span 2 years
    # 118th Congress: 2023-2024, 119th: 2025-2026, etc.
    if current_year % 2 == 0:
        # Even year, current congress started last year
        estimated_congress = 117 + (current_year - 2022) // 2
    else:
        # Odd year, new congress started this year
        estimated_congress = 117 + (current_year - 2023) // 2

    return estimated_congress

def find_upper_limit(method: str = "auto") -> int:
    """
    Find the upper limit for congress numbers.

    Args:
        method: Method to use ("config", "data", "estimate", "auto")

    Returns:
        Upper limit congress number
    """
    if method == "config":
        return get_upper_limit_from_config()
    elif method == "data":
        return get_upper_limit_from_data()
    elif method == "estimate":
        return estimate_upper_limit_from_current_year()
    elif method == "auto":
        # Try data first, then config, then estimate
        data_limit = get_upper_limit_from_data()
        if data_limit > 0:
            return data_limit

        config_limit = get_upper_limit_from_config()
        if config_limit > 0:
            return config_limit

        return estimate_upper_limit_from_current_year()
    else:
        raise ValueError(f"Unknown method: {method}")

def main():
    """Main function to demonstrate finding upper limits."""
    print("Finding upper limit for congress numbers...")

    # Try all methods
    config_limit = get_upper_limit_from_config()
    data_limit = get_upper_limit_from_data()
    estimate_limit = estimate_upper_limit_from_current_year()
    auto_limit = find_upper_limit("auto")

    print(f"From configuration: {config_limit}")
    print(f"From data directory: {data_limit}")
    print(f"From current year estimate: {estimate_limit}")
    print(f"Auto (best available): {auto_limit}")

    return auto_limit

if __name__ == "__main__":
    main()
