#!/usr/bin/env python3.10
"""
Code Quality Review Crew

Specialized crew for comprehensive code quality assessment including style, testing, architecture, dependencies, and accessibility.
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

# Define Agents
style_reviewer = Agent(
    role="Code Style and Quality Reviewer",
    goal="Ensure code follows best practices, PEP 8 standards, and maintainability guidelines",
    backstory="You are a senior software engineer focused on code quality, readability, and maintainability. You enforce coding standards and suggest improvements for long-term code health.",
    llm=llm,
    tools=[code_search, dir_search, file_read],
    verbose=True
)

testing_reviewer = Agent(
    role="Testing and Quality Assurance Reviewer",
    goal="Review test coverage, test quality, and suggest improvements for testing practices",
    backstory="You are a QA engineer and testing expert who ensures comprehensive test coverage, proper test design, and adherence to testing best practices.",
    llm=llm,
    tools=[code_search, dir_search, file_read],
    verbose=True
)

architecture_reviewer = Agent(
    role="Software Architecture Reviewer",
    goal="Analyze code architecture, design patterns, and suggest structural improvements",
    backstory="You are a software architect with expertise in design patterns, system architecture, and scalable software design principles.",
    llm=llm,
    tools=[code_search, dir_search, file_read],
    verbose=True
)

dependency_reviewer = Agent(
    role="Dependency and License Reviewer",
    goal="Review project dependencies, licenses, and security vulnerabilities in third-party packages",
    backstory="You are a dependency management expert who reviews package licenses, checks for vulnerabilities, and ensures compliance with open-source standards.",
    llm=llm,
    tools=[code_search, dir_search, file_read],
    verbose=True
)

accessibility_reviewer = Agent(
    role="Accessibility and Usability Reviewer",
    goal="Review code for accessibility compliance and user experience considerations",
    backstory="You are an accessibility expert who ensures software meets WCAG guidelines and provides inclusive user experiences.",
    llm=llm,
    tools=[code_search, dir_search, file_read],
    verbose=True
)

# Define Tasks
style_task = Task(
    description="Check code style compliance with PEP 8, naming conventions, code structure, and best practices. Identify areas for improvement in readability and maintainability.",
    expected_output="Code style review with specific recommendations for improvements, including line-by-line suggestions where applicable.",
    agent=style_reviewer
)

testing_task = Task(
    description="Review test files for coverage, quality, and best practices. Check for unit tests, integration tests, and proper test structure.",
    expected_output="Testing review report with coverage analysis, test quality assessment, and recommendations for improving test suite.",
    agent=testing_reviewer
)

architecture_task = Task(
    description="Analyze the overall code architecture, identify design patterns used, and suggest improvements for scalability and maintainability.",
    expected_output="Architecture review report with analysis of design patterns, structural recommendations, and potential refactoring suggestions.",
    agent=architecture_reviewer
)

dependency_task = Task(
    description="Review project dependencies in pyproject.toml/requirements.txt, check for outdated packages, security vulnerabilities, and license compatibility.",
    expected_output="Dependency review report with vulnerability assessments, update recommendations, and license compliance check.",
    agent=dependency_reviewer
)

accessibility_task = Task(
    description="Review code for accessibility considerations, including UI components, error messages, and user interaction patterns.",
    expected_output="Accessibility review report with WCAG compliance assessment and recommendations for improving user accessibility.",
    agent=accessibility_reviewer
)

# Create Quality Review Crew
quality_crew = Crew(
    agents=[style_reviewer, testing_reviewer, architecture_reviewer, dependency_reviewer, accessibility_reviewer],
    tasks=[style_task, testing_task, architecture_task, dependency_task, accessibility_task],
    verbose=True
)

def main():
    """Run the quality review crew."""
    print("Starting Code Quality Review Crew...")

    # Run the crew
    result = quality_crew.kickoff()

    print("\n=== Code Quality Review Results ===")
    print(result)

if __name__ == "__main__":
    main()