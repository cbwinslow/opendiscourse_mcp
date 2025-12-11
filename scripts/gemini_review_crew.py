#!/usr/bin/env python3
"""
Google Gemini Code Review

Uses Google Gemini AI for comprehensive code review.
"""

import os
import google.generativeai as genai
import argparse
import subprocess
import sys

def get_pr_diff():
    """Fetches the diff of the current pull request."""
    try:
        # These environment variables are provided by GitHub Actions
        base_sha = os.getenv("GITHUB_BASE_REF")
        head_sha = os.getenv("GITHUB_SHA")

        if not base_sha or not head_sha:
            print("GITHUB_BASE_REF or GITHUB_SHA not found. Cannot fetch diff.", file=sys.stderr)
            return None

        # Ensure we have both branches fetched
        subprocess.run(["git", "fetch", "origin", base_sha], check=True)
        subprocess.run(["git", "fetch", "origin", head_sha], check=True)
        
        # Get the diff between the base and head of the PR
        result = subprocess.run(
            ["git", "diff", f"origin/{base_sha}", head_sha],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting PR diff: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred while getting PR diff: {e}", file=sys.stderr)
        return None

def main():
    """Run Gemini code review."""
    parser = argparse.ArgumentParser(description="Run Google Gemini code review.")
    parser.add_argument("--review_type", type=str, default="all",
                        help="Type of review to run (e.g., all, security, performance, quality, documentation).")
    args = parser.parse_args()

    print(f"Starting Google Gemini Code Review for type: {args.review_type}...")

    # Configure Gemini
    genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

    # Create model
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Fetch the diff
    pr_diff = get_pr_diff()
    if not pr_diff:
        print("No diff found or error fetching diff. Exiting Gemini review.")
        sys.exit(1)

    # Base prompt for code review
    base_prompt = f"""
    You are an expert code reviewer. Analyze the provided code changes (diff below) and give constructive feedback.
    Focus on:
    1. Code quality and best practices
    2. Potential bugs or issues
    3. Readability and maintainability

    Codebase context:
    - This is a Python project for MCP servers accessing government data.
    - Main scripts are in the scripts/ directory.
    - Tests are in the tests/ directory.
    - Configuration in config/ and pyproject.toml.

    ---
    Code Diff:
    {pr_diff}
    ---
    """

    # Customize prompt based on review_type
    if args.review_type == "security":
        prompt = f"{base_prompt}\n\nSpecifically, prioritize identifying security vulnerabilities and recommending fixes."
    elif args.review_type == "performance":
        prompt = f"{base_prompt}\n\nSpecifically, prioritize identifying performance bottlenecks and suggesting optimizations."
    elif args.review_type == "documentation":
        prompt = f"{base_prompt}\n\nSpecifically, prioritize assessing documentation quality, suggesting improvements, and generating missing documentation."
    elif args.review_type == "testing":
        prompt = f"{base_prompt}\n\nSpecifically, prioritize recommending new tests, identifying edge cases, and reviewing existing test coverage."
    elif args.review_type == "quality": # Catch-all for general quality
        prompt = base_prompt
    elif args.review_type == "all": # Catch-all for general quality
        prompt = f"{base_prompt}\n\nProvide a comprehensive review covering all aspects."
    else:
        prompt = base_prompt # Default to general review

    try:
        response = model.generate_content(prompt)
        print("\n=== Google Gemini Code Review Results ===")
        print(response.text)

    except Exception as e:
        print(f"Error running Gemini review: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()