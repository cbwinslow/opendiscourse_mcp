#!/usr/bin/env python3
"""
Google Gemini Code Review

Uses Google Gemini AI for comprehensive code review.
"""

import os
import google.generativeai as genai

def main():
    """Run Gemini code review."""
    print("Starting Google Gemini Code Review...")

    # Configure Gemini
    genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

    # Create model
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Prompt for code review
    prompt = """
    You are an expert code reviewer. Analyze the following codebase and provide a comprehensive review covering:
    1. Code quality and best practices
    2. Potential bugs or issues
    3. Security vulnerabilities
    4. Performance optimizations
    5. Documentation quality
    6. Testing recommendations

    Codebase structure:
    - This is a Python project for MCP servers accessing government data
    - Main scripts in scripts/ directory
    - Tests in tests/ directory
    - Configuration in config/ and pyproject.toml

    Please provide detailed, actionable feedback.
    """

    try:
        response = model.generate_content(prompt)
        print("\n=== Google Gemini Code Review Results ===")
        print(response.text)

    except Exception as e:
        print(f"Error running Gemini review: {e}")

if __name__ == "__main__":
    main()