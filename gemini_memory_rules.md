# Gemini Memory Protocol

This document outlines the internal rules for creating, storing, and utilizing memories to ensure continuity and learning across sessions.

## 1. When to Create Memories

Memories should be created to capture key information that will be useful for future interactions. This includes:

- **User Preferences:** Explicit user preferences, such as preferred coding languages, frameworks, or communication styles.
- **Project Context:** Important details about a project, such as the project's goals, key architectural decisions, and important file locations. This also includes information about the project's dependencies and how to build/run it.
- **Session Summaries:** At the end of a session, a summary of the key outcomes, decisions, and unresolved issues should be created.
- **Key Facts and Constraints:** Any important facts or constraints that are mentioned by the user, such as "don't use library X" or "the database is on a remote server".
- **Corrections and Feedback:** When the user corrects me, I should create a memory of the correction to avoid making the same mistake again.
- **Complex Solutions:** For complex problems, I should create a memory of the solution, including the steps taken to arrive at it.

## 2. How to Create Memories

Memories should be created in a structured and consistent way to make them easy to retrieve and understand.

- **Use the `addMemory` tool:** The primary tool for creating memories is the `addMemory` tool.
- **Be Concise and Clear:** Memories should be concise and clear. Avoid storing long, rambling text.
- **Use Key-Value Pairs:** When possible, memories should be stored as key-value pairs, where the key is a short, descriptive title and the value is the information to be remembered.
- **Include Context:** When storing a memory, include enough context to make it understandable in the future. For example, if storing a code snippet, include a comment explaining what it does and where it came from.

## 3. Memory Loading and Usage

On each new instance, I will load and review all existing memories to ensure I have the full context of our previous interactions.

- **Review all memories at the start of a session:** This will help me to "remember" our previous conversations and provide a more personalized experience.
- **Use memories to inform my responses:** I will use the information stored in my memories to inform my responses and actions. For example, if a user has previously expressed a preference for a certain coding style, I will try to adhere to that style.
- **Do not be rigid:** Memories are a guide, not a straight-jacket. I will use my judgment to decide when to apply the information from my memories and when to deviate from it.

## 4. Memory Maintenance

Memories should be reviewed and updated regularly to ensure they are still relevant and accurate.

- **Review and update memories as needed:** If I learn new information that contradicts or updates an existing memory, I will update the memory accordingly.
- **Archive old memories:** Old or irrelevant memories will be archived to keep the active memory set clean and focused.
