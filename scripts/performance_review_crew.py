#!/usr/bin/env python3.10
"""
Performance Code Review Crew

Specialized crew for performance analysis and optimization.
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

# Define Performance Reviewer Agent
performance_reviewer = Agent(
    role="Performance Code Reviewer",
    goal="Analyze code for performance bottlenecks and optimization opportunities",
    backstory="You are a performance engineering expert with deep knowledge of Python optimization techniques, algorithmic complexity, and efficient coding practices.",
    llm=llm,
    tools=[code_search, dir_search, file_read],
    verbose=True
)

# Define Performance Task
performance_task = Task(
    description="Analyze the code for performance issues such as inefficient algorithms, memory leaks, unnecessary computations, and database query optimizations.",
    expected_output="Performance analysis report with identified bottlenecks, optimization suggestions, and estimated impact.",
    agent=performance_reviewer
)

# Create Performance Review Crew
performance_crew = Crew(
    agents=[performance_reviewer],
    tasks=[performance_task],
    verbose=True
)

def main():
    """Run the performance review crew."""
    print("Starting Performance Code Review Crew...")

    # Run the crew
    result = performance_crew.kickoff()

    print("\n=== Performance Review Results ===")
    print(result)

if __name__ == "__main__":
    main()