#!/usr/bin/env python3.10
"""
Security Code Review Crew

Specialized crew for security analysis and vulnerability assessment.
"""

import os
import sys
from crewai import Agent, Task, Crew
from crewai_tools import CodeDocsSearchTool, DirectorySearchTool, FileReadTool
from langchain_openai import ChatOpenAI
from langfuse.callback import CallbackHandler

# Initialize Langfuse for observability
langfuse_handler = CallbackHandler()

# Initialize LLM with Langfuse tracing
llm = ChatOpenAI(
    model="microsoft/wizardlm-2-8x22b:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.1,
    callbacks=[langfuse_handler]
)

# Define Tools
code_search = CodeDocsSearchTool()
dir_search = DirectorySearchTool()
file_read = FileReadTool()

# Define Security Reviewer Agent
security_reviewer = Agent(
    role="Security Code Reviewer",
    goal="Identify potential security vulnerabilities and suggest fixes",
    backstory="You are an expert cybersecurity analyst specializing in code security. You have extensive experience in identifying vulnerabilities in Python applications and providing actionable remediation steps.",
    llm=llm,
    tools=[code_search, dir_search, file_read],
    verbose=True
)

# Define Security Task
security_task = Task(
    description="Review the codebase for security vulnerabilities including SQL injection, XSS, authentication issues, and other common security flaws. Provide specific recommendations for fixes.",
    expected_output="A detailed security review report with identified vulnerabilities, severity levels, and remediation steps.",
    agent=security_reviewer
)

# Create Security Review Crew
security_crew = Crew(
    agents=[security_reviewer],
    tasks=[security_task],
    verbose=True
)

def main():
    """Run the security review crew."""
    print("Starting Security Code Review Crew...")

    # Run the crew
    result = security_crew.kickoff()

    print("\n=== Security Review Results ===")
    print(result)

if __name__ == "__main__":
    main()