#!/usr/bin/env python3.10
"""
Documentation Review Crew

Specialized crew for documentation quality assessment and improvement suggestions.
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

# Define Documentation Reviewer Agent
documentation_reviewer = Agent(
    role="Documentation Reviewer",
    goal="Review and suggest improvements for code documentation and comments",
    backstory="You are a technical writer and documentation specialist who ensures that code is well-documented, with clear docstrings, comments, and README updates.",
    llm=llm,
    tools=[code_search, dir_search, file_read],
    verbose=True
)

# Define Documentation Task
documentation_task = Task(
    description="Review documentation quality including docstrings, comments, README files, and API documentation. Suggest additions or improvements.",
    expected_output="Documentation review report with recommendations for enhancing code documentation and user guides.",
    agent=documentation_reviewer
)

# Create Documentation Review Crew
documentation_crew = Crew(
    agents=[documentation_reviewer],
    tasks=[documentation_task],
    verbose=True
)

def main():
    """Run the documentation review crew."""
    print("Starting Documentation Review Crew...")

    # Run the crew
    result = documentation_crew.kickoff()

    print("\n=== Documentation Review Results ===")
    print(result)

if __name__ == "__main__":
    main()