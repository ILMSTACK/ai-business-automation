"""
Prompt templates for business automation AI generation
Keeps all prompts separate from business logic for better maintainability
"""
from datetime import datetime, UTC

def get_testcase_generation_prompt(user_story_content):
    """Primary detailed prompt for test case generation"""
    return f"""You are a senior QA engineer creating comprehensive test cases for a user story.

USER STORY:
{user_story_content}

Generate appropriate test cases based on the complexity and scope of this user story. Consider:
- Positive/happy path scenarios
- Negative/error scenarios  
- Edge cases and boundary conditions
- Security considerations if applicable
- Performance considerations if applicable

CRITICAL: Return ONLY a valid JSON array with this exact structure:
[
  {{
    "title": "Clear test case title",
    "description": "Detailed description of what this test validates", 
    "steps": ["Step 1 action", "Step 2 action", "Step 3 action"],
    "expected_result": "Clear expected outcome",
    "priority": "LOW|MEDIUM|HIGH|CRITICAL",
    "type": "FUNCTIONAL|PERFORMANCE|SECURITY|NEGATIVE|VALIDATION"
  }}
]

IMPORTANT: Use EXACT priority values: LOW, MEDIUM, HIGH, CRITICAL
IMPORTANT: Use EXACT type values: FUNCTIONAL, PERFORMANCE, SECURITY, NEGATIVE, VALIDATION

Generate an appropriate number of test cases (typically 3-8 depending on complexity).
Ensure each test case is thorough, realistic, and covers different scenarios.
Return ONLY the JSON array, no other text."""

def get_testcase_retry_prompt(user_story_content):
    """Simpler retry prompt for test case generation"""
    return f"""Create test cases for this user story in JSON format:

USER STORY: {user_story_content}

Return exactly this JSON structure with no extra text:
[
  {{
    "title": "Test case name",
    "description": "What this test does",
    "steps": ["action 1", "action 2", "action 3"],
    "expected_result": "what should happen",
    "priority": "HIGH",
    "type": "FUNCTIONAL"
  }}
]

Use priority: LOW, MEDIUM, HIGH, or CRITICAL
Use type: FUNCTIONAL, PERFORMANCE, SECURITY, NEGATIVE, or VALIDATION
Create 3-6 test cases covering main functionality and error cases."""

def get_testcase_final_prompt(user_story_content):
    """Most basic prompt as final retry"""
    return f"""JSON test cases for: {user_story_content}

Format:
[{{"title":"Basic Test","description":"Test description","steps":["step1","step2"],"expected_result":"result","priority":"HIGH","type":"FUNCTIONAL"}}]

Return only JSON array."""

def get_task_generation_prompt(user_story_content, available_users=None):
    """Primary detailed prompt for task generation with user assignment and due dates (Option A)."""
    now_utc = datetime.now(UTC).isoformat()

    user_context = ""
    if available_users and len(available_users) > 0:
        user_list = []
        for user in available_users:
            role_name = user.get('role', {}).get('role_name', 'Unknown') if user.get('role') else 'Unknown'
            user_list.append(f"- {user['email']} ({role_name})")
        user_context = f"""
AVAILABLE TEAM MEMBERS FOR ASSIGNMENT:
{chr(10).join(user_list)}

You can assign tasks to any of these team members by using their email address, or use "Unassigned" if no specific assignment is needed.
"""
    else:
        user_context = """
No team members are currently available in the system. Use "Unassigned" for all tasks.
"""

    return f"""You are a senior project manager breaking down a user story into development tasks.

TODAY_UTC: {now_utc}
NEVER output a due_date earlier than TODAY_UTC.

USER STORY:
{user_story_content}

{user_context}

Create a comprehensive task breakdown covering the full development lifecycle. Consider:
- Backend API development
- Frontend UI implementation
- Database changes (if needed)
- Testing tasks (unit, integration)
- Documentation updates
- Code review and deployment tasks
- Security considerations
- Performance optimization (if applicable)

DUE DATE RULES:
- Choose realistic near-term target dates based on priority (no dates in the past):
  - CRITICAL: within 1–2 days
  - HIGH: within 3–5 days
  - MEDIUM: within 5–7 days
  - LOW: within 7–14 days
- Prefer ISO 8601 with timezone (e.g., "2025-09-05T17:00:00Z").
- If you only provide a date (YYYY-MM-DD), it will be treated as end-of-day.

CRITICAL: Return ONLY a valid JSON array with this exact structure:
[
  {{
    "title": "Clear task title",
    "description": "Detailed task description with specific deliverables",
    "assignee": "user@example.com or Unassigned",
    "priority": "LOW|MEDIUM|HIGH|CRITICAL",
    "estimated_hours": 4.5,
    "labels": ["backend", "api", "development"],
    "due_date": "YYYY-MM-DD or ISO 8601 (e.g., 2025-09-05 or 2025-09-05T17:00:00Z)"
  }}
]

IMPORTANT: Use EXACT priority values: LOW, MEDIUM, HIGH, CRITICAL
IMPORTANT: For assignee, use either an email from the available team members list above, or "Unassigned"

Generate an appropriate number of tasks (typically 4-10 depending on story complexity).
Estimate realistic hours for each task.
Use relevant labels like: backend, frontend, database, testing, documentation, security, etc.
Assign tasks to appropriate team members based on their roles and the task type.
Return ONLY the JSON array, no other text."""

def get_task_retry_prompt(user_story_content, available_users=None):
    """Simpler retry prompt for task generation"""

    # Build simplified user context
    user_context = ""
    if available_users and len(available_users) > 0:
        emails = [user['email'] for user in available_users]
        user_context = f"Available users: {', '.join(emails[:5])}{'...' if len(emails) > 5 else ''} or use 'Unassigned'"
    else:
        user_context = "Use 'Unassigned' for assignee"

    return f"""Create development tasks for this user story in JSON format:

USER STORY: {user_story_content}

{user_context}

Return exactly this JSON structure with no extra text:
[
  {{
    "title": "Task name", 
    "description": "What needs to be done",
    "assignee": "user@example.com or Unassigned",
    "priority": "HIGH",
    "estimated_hours": 4.0,
    "labels": ["development", "backend"]
  }}
]

Use priority: LOW, MEDIUM, HIGH, or CRITICAL
Create 4-8 tasks covering development, testing, and documentation."""

def get_task_final_prompt(user_story_content, available_users=None):
    """Most basic prompt as final retry"""
    return f"""JSON development tasks for: {user_story_content}

Format:
[{{"title":"Development Task","description":"Task description","assignee":"Unassigned","priority":"HIGH","estimated_hours":4.0,"labels":["development"]}}]

Return only JSON array."""