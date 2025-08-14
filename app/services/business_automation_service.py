import json
import time
from datetime import datetime
from ..repositories.business_automation_repository import BusinessAutomationRepository
from ..services.ollama_service import chat
from ..services.automation_prompts import (
    get_testcase_generation_prompt,
    get_testcase_retry_prompt,
    get_testcase_final_prompt,
    get_task_generation_prompt,
    get_task_retry_prompt,
    get_task_final_prompt
)


class BusinessAutomationService:
    """Service for business automation logic - uses Repository for all database operations"""

    @staticmethod
    def create_user_story_and_generate(user_story_content, title):
        """
        Main workflow:
        1. Save user story to database
        2. Generate testcases using Ollama
        3. Generate tasks using Ollama
        4. Save all to database
        5. Return complete result
        """
        try:
            # 1. Create and save user story using Repository
            user_story = BusinessAutomationRepository.create_user_story(title, user_story_content)
            user_story_id = user_story.user_story_id

            # 2. Generate testcases using Ollama AI
            start_time = time.time()
            generated_testcases = BusinessAutomationService._generate_testcases(user_story_content)
            testcase_time = time.time() - start_time

            # 3. Generate tasks using Ollama AI
            start_time = time.time()
            generated_tasks = BusinessAutomationService._generate_tasks(user_story_content)
            task_time = time.time() - start_time

            # 4. Save generated content using Repository
            testcase_objects = []
            for tc in generated_testcases:
                testcase = BusinessAutomationRepository.create_testcase(
                    user_story_id=user_story_id,
                    title=tc['title'],
                    description=tc['description'],
                    steps=tc['steps'],
                    expected_result=tc['expected_result'],
                    priority_code=tc['priority'],  # Will be converted to ID in repository
                    test_type_code=tc['type']  # Will be converted to ID in repository
                )
                testcase_objects.append(testcase)

            task_objects = []
            for task_data in generated_tasks:
                task = BusinessAutomationRepository.create_task(
                    user_story_id=user_story_id,
                    title=task_data['title'],
                    description=task_data['description'],
                    assignee_email=task_data.get('assignee', 'Unassigned'),  # Will be converted to ID in repository
                    priority_code=task_data['priority'],  # Will be converted to ID in repository
                    estimated_hours=task_data.get('estimated_hours', 0),
                    labels=','.join(task_data.get('labels', []))
                )
                task_objects.append(task)

            # 5. Log the generation activity using Repository
            BusinessAutomationRepository.create_generation_log(
                user_story_id=user_story_id,
                log_type_code='COMPLETE',  # Will be converted to ID in repository
                status_code='SUCCESS',  # Will be converted to ID in repository
                items_generated=len(testcase_objects) + len(task_objects),
                processing_time=testcase_time + task_time
            )

            # 6. Commit all changes using Repository
            BusinessAutomationRepository.commit_transaction()

            # 7. Return complete result
            return {
                'user_story_id': user_story_id,
                'data': {
                    'testcases': [BusinessAutomationService._safe_to_dict(tc) for tc in testcase_objects],
                    'tasks': [BusinessAutomationService._safe_to_dict(task) for task in task_objects]
                }
            }

        except Exception as e:
            # Rollback on error
            BusinessAutomationRepository.rollback_transaction()
            raise Exception(f"Failed to create user story and generate content: {str(e)}")

    @staticmethod
    def _generate_testcases(user_story_content):
        """
        Generate test cases using Ollama AI with retry logic
        """
        # Define prompt strategies in order of preference
        prompt_strategies = [
            get_testcase_generation_prompt,
            get_testcase_retry_prompt,
            get_testcase_final_prompt
        ]

        for attempt, get_prompt in enumerate(prompt_strategies, 1):
            try:
                # Get the prompt for this attempt
                prompt = get_prompt(user_story_content)

                # Call Ollama
                response = chat(prompt)

                if not response.get('ok'):
                    print(f"Ollama error on attempt {attempt}: {response.get('error')}")
                    continue

                # Parse and validate JSON response
                reply = response.get('reply', '').strip()
                testcases = BusinessAutomationService._parse_and_validate_testcases(reply)

                if testcases:
                    print(f"Successfully generated {len(testcases)} test cases on attempt {attempt}")
                    return testcases

            except Exception as e:
                print(f"Test case generation attempt {attempt} failed: {str(e)}")
                continue

        # If all attempts failed, raise error
        raise Exception("Failed to generate test cases after all retry attempts")

    @staticmethod
    def _generate_tasks(user_story_content):
        """
        Generate development tasks using Ollama AI with retry logic
        """
        # Get available users for assignment
        try:
            available_users = BusinessAutomationRepository.get_all_active_users()
            print(f"DEBUG: Found {len(available_users)} users")
        except Exception as e:
            print(f"DEBUG: Error getting users: {e}")
            print(f"DEBUG: Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            available_users = []

        # Define prompt strategies in order of preference
        prompt_strategies = [
            lambda content: get_task_generation_prompt(content, available_users),
            lambda content: get_task_retry_prompt(content, available_users),
            lambda content: get_task_final_prompt(content, available_users)
        ]

        for attempt, get_prompt in enumerate(prompt_strategies, 1):
            try:
                # Get the prompt for this attempt
                prompt = get_prompt(user_story_content)

                # Call Ollama
                response = chat(prompt)

                if not response.get('ok'):
                    print(f"Ollama error on attempt {attempt}: {response.get('error')}")
                    continue

                # Parse and validate JSON response
                reply = response.get('reply', '').strip()
                tasks = BusinessAutomationService._parse_and_validate_tasks(reply)

                if tasks:
                    print(f"Successfully generated {len(tasks)} tasks on attempt {attempt}")
                    return tasks

            except Exception as e:
                print(f"Task generation attempt {attempt} failed: {str(e)}")
                continue

        # If all attempts failed, raise error
        raise Exception("Failed to generate tasks after all retry attempts")

    @staticmethod
    def _parse_and_validate_testcases(json_text):
        """
        Parse and validate test case JSON response with updated validation for lookup values
        """
        try:
            # Clean up the response - remove any markdown formatting
            json_text = json_text.replace('```json', '').replace('```', '').strip()

            # Parse JSON
            testcases = json.loads(json_text)

            # Validate structure
            if not isinstance(testcases, list):
                return None

            # Get valid lookup values from database
            priorities = BusinessAutomationRepository.get_all_priorities()
            valid_priorities = [p.priority_code for p in priorities]

            categories = BusinessAutomationRepository.get_all_categories()
            valid_types = [c.ctgry_code for c in categories if
                           c.ctgry_code in ['FUNCTIONAL', 'PERFORMANCE', 'SECURITY', 'NEGATIVE', 'VALIDATION']]

            validated_testcases = []
            for tc in testcases:
                if not isinstance(tc, dict):
                    continue

                # Validate required fields
                required_fields = ['title', 'description', 'steps', 'expected_result', 'priority', 'type']
                if not all(field in tc for field in required_fields):
                    continue

                # Normalize priority and type to uppercase for consistency
                priority_upper = tc['priority'].upper()
                type_upper = tc['type'].upper()

                # Validate field types and values with database lookup values
                if (isinstance(tc['title'], str) and tc['title'].strip() and
                        isinstance(tc['description'], str) and tc['description'].strip() and
                        isinstance(tc['steps'], list) and len(tc['steps']) > 0 and
                        isinstance(tc['expected_result'], str) and tc['expected_result'].strip() and
                        priority_upper in valid_priorities and
                        type_upper in valid_types):
                    # Normalize the values
                    tc['priority'] = priority_upper
                    tc['type'] = type_upper
                    validated_testcases.append(tc)

            return validated_testcases if validated_testcases else None

        except json.JSONDecodeError:
            return None
        except Exception:
            return None

    @staticmethod
    def _parse_and_validate_tasks(json_text):
        """
        Parse and validate task JSON response with updated validation for lookup values
        """
        try:
            # Clean up the response - remove any markdown formatting
            json_text = json_text.replace('```json', '').replace('```', '').strip()

            # Parse JSON
            tasks = json.loads(json_text)

            # Validate structure
            if not isinstance(tasks, list):
                return None

            # Get valid priority values from database
            priorities = BusinessAutomationRepository.get_all_priorities()
            valid_priorities = [p.priority_code for p in priorities]

            validated_tasks = []
            for task in tasks:
                if not isinstance(task, dict):
                    continue

                # Validate required fields
                required_fields = ['title', 'description', 'priority', 'estimated_hours', 'labels']
                if not all(field in task for field in required_fields):
                    continue

                # Normalize priority to uppercase for consistency
                priority_upper = task['priority'].upper()

                # Validate field types and values
                if (isinstance(task['title'], str) and task['title'].strip() and
                        isinstance(task['description'], str) and task['description'].strip() and
                        priority_upper in valid_priorities and
                        isinstance(task['estimated_hours'], (int, float)) and task['estimated_hours'] >= 0 and
                        isinstance(task['labels'], list)):
                    # Ensure labels are strings and normalize priority
                    task['labels'] = [str(label) for label in task['labels']]
                    task['priority'] = priority_upper
                    validated_tasks.append(task)

            return validated_tasks if validated_tasks else None

        except json.JSONDecodeError:
            return None
        except Exception:
            return None

    @staticmethod
    def get_testcases_by_story_id(user_story_id):
        """Get all test cases for a specific user story"""
        try:
            testcases = BusinessAutomationRepository.get_testcases_by_story_id(user_story_id)
            if not testcases:
                return None

            return [tc.to_dict() for tc in testcases]
        except Exception as e:
            raise Exception(f"Failed to retrieve testcases: {str(e)}")

    @staticmethod
    def get_tasks_by_story_id(user_story_id):
        """Get all tasks for a specific user story"""
        try:
            tasks = BusinessAutomationRepository.get_tasks_by_story_id(user_story_id)
            if not tasks:
                return None

            return [task.to_dict() for task in tasks]
        except Exception as e:
            raise Exception(f"Failed to retrieve tasks: {str(e)}")

    @staticmethod
    def get_generation_history():
        """Get history of all user story generations"""
        try:
            # Use Repository's complex query with joins
            return BusinessAutomationRepository.get_generation_history_with_counts()
        except Exception as e:
            raise Exception(f"Failed to retrieve generation history: {str(e)}")

    @staticmethod
    def get_user_story_by_id(user_story_id):
        """Get user story details by ID"""
        try:
            user_story = BusinessAutomationRepository.get_user_story_by_id(user_story_id)
            if not user_story:
                return None

            return user_story.to_dict()
        except Exception as e:
            raise Exception(f"Failed to retrieve user story: {str(e)}")

    @staticmethod
    def get_dashboard_statistics():
        """Get comprehensive dashboard statistics"""
        try:
            return BusinessAutomationRepository.get_dashboard_statistics()
        except Exception as e:
            raise Exception(f"Failed to retrieve dashboard statistics: {str(e)}")

    @staticmethod
    def search_user_stories(search_term):
        """Search user stories"""
        try:
            user_stories = BusinessAutomationRepository.search_user_stories(search_term)
            return [story.to_dict() for story in user_stories]
        except Exception as e:
            raise Exception(f"Failed to search user stories: {str(e)}")

    @staticmethod
    def get_lookup_data():
        """Get all lookup table data for frontend dropdowns"""
        try:
            return {
                'priorities': [p.to_dict() for p in BusinessAutomationRepository.get_all_priorities()],
                'test_statuses': [s.to_dict() for s in
                                  BusinessAutomationRepository.get_all_statuses_by_category('testcase')],
                'task_statuses': [s.to_dict() for s in
                                  BusinessAutomationRepository.get_all_statuses_by_category('task')],
                'categories': [c.to_dict() for c in BusinessAutomationRepository.get_all_categories()]
            }
        except Exception as e:
            raise Exception(f"Failed to retrieve lookup data: {str(e)}")

    @staticmethod
    def _safe_to_dict(obj):
        """Safely convert model to dict, handling bytes and datetime issues"""
        import json
        from datetime import datetime

        def convert_value(value):
            """Convert problematic values to JSON-safe format"""
            if isinstance(value, bytes):
                try:
                    # Try to decode as JSON first
                    return json.loads(value.decode('utf-8'))
                except:
                    # If that fails, just decode as string
                    return value.decode('utf-8')
            elif isinstance(value, datetime):
                return value.isoformat()
            else:
                return value

        # Get the original dict
        original_dict = obj.to_dict()

        # Convert all values to be JSON-safe
        safe_dict = {}
        for key, value in original_dict.items():
            safe_dict[key] = convert_value(value)

        return safe_dict