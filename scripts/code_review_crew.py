#!/usr/bin/env python3.10
"""
CrewAI Code Review Crew

This script runs a multi-agent crew for automated code review.
The crew consists of specialized agents for different aspects of code quality.
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
security_reviewer = Agent(
    role="Security Code Reviewer",
    goal="Identify potential security vulnerabilities and suggest fixes",
    backstory="You are an expert cybersecurity analyst specializing in code security. You have extensive experience in identifying vulnerabilities in Python applications and providing actionable remediation steps.",
    llm=llm,
    tools=[code_search, dir_search],
    verbose=True
)

performance_reviewer = Agent(
    role="Performance Code Reviewer",
    goal="Analyze code for performance bottlenecks and optimization opportunities",
    backstory="You are a performance engineering expert with deep knowledge of Python optimization techniques, algorithmic complexity, and efficient coding practices.",
    llm=llm,
    tools=[code_search, dir_search],
    verbose=True
)

style_reviewer = Agent(
    role="Code Style and Quality Reviewer",
    goal="Ensure code follows best practices, PEP 8 standards, and maintainability guidelines",
    backstory="You are a senior software engineer focused on code quality, readability, and maintainability. You enforce coding standards and suggest improvements for long-term code health.",
    llm=llm,
    tools=[code_search, dir_search],
    verbose=True
)

documentation_reviewer = Agent(
    role="Documentation Reviewer",
    goal="Review and suggest improvements for code documentation and comments",
    backstory="You are a technical writer and documentation specialist who ensures that code is well-documented, with clear docstrings, comments, and README updates.",
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
security_task = Task(
    description="Review the codebase for security vulnerabilities including SQL injection, XSS, authentication issues, and other common security flaws. Provide specific recommendations for fixes.",
    expected_output="A detailed security review report with identified vulnerabilities, severity levels, and remediation steps.",
    agent=security_reviewer
)

performance_task = Task(
    description="Analyze the code for performance issues such as inefficient algorithms, memory leaks, unnecessary computations, and database query optimizations.",
    expected_output="Performance analysis report with identified bottlenecks, optimization suggestions, and estimated impact.",
    agent=performance_reviewer
)

style_task = Task(
    description="Check code style compliance with PEP 8, naming conventions, code structure, and best practices. Identify areas for improvement in readability and maintainability.",
    expected_output="Code style review with specific recommendations for improvements, including line-by-line suggestions where applicable.",
    agent=style_reviewer
)

documentation_task = Task(
    description="Review documentation quality including docstrings, comments, README files, and API documentation. Suggest additions or improvements.",
    expected_output="Documentation review report with recommendations for enhancing code documentation and user guides.",
    agent=documentation_reviewer
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

# Create Crew
code_review_crew = Crew(
    agents=[security_reviewer, performance_reviewer, style_reviewer, documentation_reviewer, testing_reviewer, architecture_reviewer, dependency_reviewer, accessibility_reviewer],
    tasks=[security_task, performance_task, style_task, documentation_task, testing_task, architecture_task, dependency_task, accessibility_task],
    verbose=True
)

def main():
    """Run the code review crew."""
    print("Starting Code Review Crew...")

    # Run the crew
    result = code_review_crew.kickoff()

    print("\n=== Code Review Results ===")
    print(result)

    # In a real implementation, you might want to post these results as PR comments
    # using GitHub API, but for now we'll just print them

if __name__ == "__main__":
    main()