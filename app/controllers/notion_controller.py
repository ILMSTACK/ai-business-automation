from flask import jsonify
from ..services.notion_service import NotionService
from ..repositories.business_automation_repository import BusinessAutomationRepository
import logging

logger = logging.getLogger(__name__)

def create_notion_task(user_story_id, task_id):
    """Create a task in Notion"""
    try:
        # Initialize repository first to get user story
        repository = BusinessAutomationRepository()
        
        # Validate that user story exists
        user_story = repository.get_user_story_by_id(user_story_id)
        if not user_story:
            return {"success": False, "error": f"User story with ID {user_story_id} not found"}, 404
        
        # Initialize NotionService with company ID
        notion_service = NotionService(com_id=user_story.com_id)
        
        # Validate that task exists and belongs to the user story
        task = repository.get_task_by_id(task_id)
        if not task:
            return {"success": False, "error": f"Task with ID {task_id} not found"}, 404
        
        if task.user_story_id != user_story_id:
            return {"success": False, "error": f"Task {task_id} does not belong to user story {user_story_id}"}, 400
        
        # Check if task already has a Notion page
        if task.notion_page_id:
            notion_url = notion_service.get_notion_page_url(task.notion_page_id)
            return {
                "success": True,
                "message": "Task already exists in Notion",
                "task_id": task_id,
                "notion_page_id": task.notion_page_id,
                "notion_url": notion_url
            }, 200
        
        # Create task in Notion
        task_data = task.to_dict()
        notion_page_id = notion_service.push_task_to_notion(task_data, user_story.user_story_title, user_story_id)
        
        # Update task with Notion page ID
        repository.update_task_notion_id(task_id, notion_page_id)
        
        notion_url = notion_service.get_notion_page_url(notion_page_id)
        
        return {
            "success": True,
            "message": "Task successfully created in Notion",
            "task_id": task_id,
            "notion_page_id": notion_page_id,
            "notion_url": notion_url
        }, 201
        
    except Exception as e:
        logger.error(f"Error creating task in Notion: {e}")
        return {"success": False, "error": f"Failed to create task in Notion: {str(e)}"}, 500

def create_notion_testcase(user_story_id, test_case_id):
    """Create a test case in Notion"""
    try:
        # Initialize repository first to get user story
        repository = BusinessAutomationRepository()
        
        # Validate that user story exists
        user_story = repository.get_user_story_by_id(user_story_id)
        if not user_story:
            return {"success": False, "error": f"User story with ID {user_story_id} not found"}, 404
        
        # Initialize NotionService with company ID
        notion_service = NotionService(com_id=user_story.com_id)
        
        # Validate that test case exists and belongs to the user story
        test_case = repository.get_testcase_by_id(test_case_id)
        if not test_case:
            return {"success": False, "error": f"Test case with ID {test_case_id} not found"}, 404
        
        if test_case.user_story_id != user_story_id:
            return {"success": False, "error": f"Test case {test_case_id} does not belong to user story {user_story_id}"}, 400
        
        # Check if test case already has a Notion page
        if test_case.notion_page_id:
            notion_url = notion_service.get_notion_page_url(test_case.notion_page_id)
            return {
                "success": True,
                "message": "Test case already exists in Notion",
                "test_case_id": test_case_id,
                "notion_page_id": test_case.notion_page_id,
                "notion_url": notion_url
            }, 200
        
        # Create test case in Notion
        testcase_data = test_case.to_dict()
        notion_page_id = notion_service.push_testcase_to_notion(testcase_data, user_story.user_story_title, user_story_id)
        
        # Update test case with Notion page ID
        repository.update_testcase_notion_id(test_case_id, notion_page_id)
        
        notion_url = notion_service.get_notion_page_url(notion_page_id)
        
        return {
            "success": True,
            "message": "Test case successfully created in Notion",
            "test_case_id": test_case_id,
            "notion_page_id": notion_page_id,
            "notion_url": notion_url
        }, 201
        
    except Exception as e:
        logger.error(f"Error creating test case in Notion: {e}")
        return {"success": False, "error": f"Failed to create test case in Notion: {str(e)}"}, 500

def sync_notion_task(user_story_id, task_id):
    """Sync task updates from Notion to local database"""
    try:
        # Initialize repository first to get user story
        repository = BusinessAutomationRepository()
        
        # Validate that user story exists
        user_story = repository.get_user_story_by_id(user_story_id)
        if not user_story:
            return {"success": False, "error": f"User story with ID {user_story_id} not found"}, 404
        
        # Initialize NotionService with company ID
        notion_service = NotionService(com_id=user_story.com_id)
        
        # Validate that task exists and belongs to the user story
        task = repository.get_task_by_id(task_id)
        if not task:
            return {"success": False, "error": f"Task with ID {task_id} not found"}, 404
        
        if task.user_story_id != user_story_id:
            return {"success": False, "error": f"Task {task_id} does not belong to user story {user_story_id}"}, 400
        
        # Check if task has a Notion page
        if not task.notion_page_id:
            logger.warning(f"Task {task_id} has no notion_page_id. This task may have been created before Notion integration.")
            return {"success": False, "error": "Task does not have an associated Notion page. Create it in Notion first using the create endpoint."}, 400
        
        # Sync data from Notion (notion_page_id is actually the database entry ID)
        notion_data = notion_service.sync_task_from_notion(task.notion_page_id)
        
        # Update local task with Notion data
        updated_task = repository.update_task_from_notion_sync(task_id, notion_data)
        
        return {
            "success": True,
            "message": "Task successfully synced from Notion and updated in local database",
            "task_id": task_id,
            "notion_page_id": task.notion_page_id,
            "synced_data": notion_data,
            "updated_task": updated_task.to_dict() if updated_task else None
        }, 200
        
    except Exception as e:
        logger.error(f"Error syncing task from Notion: {e}")
        return {"success": False, "error": f"Failed to sync task from Notion: {str(e)}"}, 500

def sync_notion_testcase(user_story_id, test_case_id):
    """Sync test case updates from Notion to local database"""
    try:
        # Initialize repository first to get user story
        repository = BusinessAutomationRepository()
        
        # Validate that user story exists
        user_story = repository.get_user_story_by_id(user_story_id)
        if not user_story:
            return {"success": False, "error": f"User story with ID {user_story_id} not found"}, 404
        
        # Initialize NotionService with company ID
        notion_service = NotionService(com_id=user_story.com_id)
        
        # Validate that test case exists and belongs to the user story
        test_case = repository.get_testcase_by_id(test_case_id)
        if not test_case:
            return {"success": False, "error": f"Test case with ID {test_case_id} not found"}, 404
        
        if test_case.user_story_id != user_story_id:
            return {"success": False, "error": f"Test case {test_case_id} does not belong to user story {user_story_id}"}, 400
        
        # Check if test case has a Notion page
        if not test_case.notion_page_id:
            logger.warning(f"Test case {test_case_id} has no notion_page_id. This test case may have been created before Notion integration.")
            return {"success": False, "error": "Test case does not have an associated Notion page. Create it in Notion first using the create endpoint."}, 400
        
        # Debug logging
        logger.info(f"Syncing test case {test_case_id} with notion_page_id: {test_case.notion_page_id}")
        
        # Sync data from Notion (notion_page_id is actually the database entry ID)
        notion_data = notion_service.sync_testcase_from_notion(test_case.notion_page_id)
        
        logger.info(f"Synced data from Notion: {notion_data}")
        
        # Update local test case with Notion data
        updated_testcase = repository.update_testcase_from_notion_sync(test_case_id, notion_data)
        
        return {
            "success": True,
            "message": "Test case successfully synced from Notion and updated in local database",
            "test_case_id": test_case_id,
            "notion_page_id": test_case.notion_page_id,
            "synced_data": notion_data,
            "updated_testcase": updated_testcase.to_dict() if updated_testcase else None
        }, 200
        
    except Exception as e:
        logger.error(f"Error syncing test case from Notion: {e}")
        return {"success": False, "error": f"Failed to sync test case from Notion: {str(e)}"}, 500

def create_notion_all_tasks(user_story_id):
    """Create all tasks for a user story in Notion"""
    try:
        # Initialize repository first to get user story
        repository = BusinessAutomationRepository()
        
        # Validate that user story exists
        user_story = repository.get_user_story_by_id(user_story_id)
        if not user_story:
            return {"success": False, "error": f"User story with ID {user_story_id} not found"}, 404
        
        # Initialize NotionService with company ID
        notion_service = NotionService(com_id=user_story.com_id)
        
        # Get all tasks for the user story
        tasks = repository.get_tasks_by_user_story_id(user_story_id)
        if not tasks:
            return {"success": False, "error": f"No tasks found for user story {user_story_id}"}, 404
        
        results = []
        success_count = 0
        error_count = 0
        
        for task in tasks:
            try:
                # Skip if already has Notion page
                if task.notion_page_id:
                    results.append({
                        "task_id": task.task_id,
                        "status": "skipped",
                        "message": "Task already exists in Notion",
                        "notion_url": notion_service.get_notion_page_url(task.notion_page_id)
                    })
                    continue
                
                # Create task in Notion
                task_data = task.to_dict()
                notion_page_id = notion_service.push_task_to_notion(task_data, user_story.user_story_title, user_story_id)
                
                # Update task with Notion page ID
                repository.update_task_notion_id(task.task_id, notion_page_id)
                
                notion_url = notion_service.get_notion_page_url(notion_page_id)
                
                results.append({
                    "task_id": task.task_id,
                    "status": "created",
                    "notion_page_id": notion_page_id,
                    "notion_url": notion_url
                })
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error creating task {task.task_id} in Notion: {e}")
                results.append({
                    "task_id": task.task_id,
                    "status": "error",
                    "error": str(e)
                })
                error_count += 1
        
        return {
            "success": error_count == 0,
            "message": f"Bulk task creation completed. {success_count} created, {error_count} failed",
            "user_story_id": user_story_id,
            "total_tasks": len(tasks),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }, 200 if error_count == 0 else 207  # 207 Multi-Status if there were some errors
        
    except Exception as e:
        logger.error(f"Error creating all tasks in Notion: {e}")
        return {"success": False, "error": f"Failed to create tasks in Notion: {str(e)}"}, 500

def create_notion_all_testcases(user_story_id):
    """Create all test cases for a user story in Notion"""
    try:
        # Initialize repository first to get user story
        repository = BusinessAutomationRepository()
        
        # Validate that user story exists
        user_story = repository.get_user_story_by_id(user_story_id)
        if not user_story:
            return {"success": False, "error": f"User story with ID {user_story_id} not found"}, 404
        
        # Initialize NotionService with company ID
        notion_service = NotionService(com_id=user_story.com_id)
        
        # Get all test cases for the user story
        test_cases = repository.get_testcases_by_user_story_id(user_story_id)
        if not test_cases:
            return {"success": False, "error": f"No test cases found for user story {user_story_id}"}, 404
        
        results = []
        success_count = 0
        error_count = 0
        
        for test_case in test_cases:
            try:
                # Skip if already has Notion page
                if test_case.notion_page_id:
                    results.append({
                        "test_case_id": test_case.test_case_id,
                        "status": "skipped",
                        "message": "Test case already exists in Notion",
                        "notion_url": notion_service.get_notion_page_url(test_case.notion_page_id)
                    })
                    continue
                
                # Create test case in Notion
                testcase_data = test_case.to_dict()
                notion_page_id = notion_service.push_testcase_to_notion(testcase_data, user_story.user_story_title, user_story_id)
                
                # Update test case with Notion page ID
                repository.update_testcase_notion_id(test_case.test_case_id, notion_page_id)
                
                notion_url = notion_service.get_notion_page_url(notion_page_id)
                
                results.append({
                    "test_case_id": test_case.test_case_id,
                    "status": "created",
                    "notion_page_id": notion_page_id,
                    "notion_url": notion_url
                })
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error creating test case {test_case.test_case_id} in Notion: {e}")
                results.append({
                    "test_case_id": test_case.test_case_id,
                    "status": "error",
                    "error": str(e)
                })
                error_count += 1
        
        return {
            "success": error_count == 0,
            "message": f"Bulk test case creation completed. {success_count} created, {error_count} failed",
            "user_story_id": user_story_id,
            "total_test_cases": len(test_cases),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }, 200 if error_count == 0 else 207  # 207 Multi-Status if there were some errors
        
    except Exception as e:
        logger.error(f"Error creating all test cases in Notion: {e}")
        return {"success": False, "error": f"Failed to create test cases in Notion: {str(e)}"}, 500

def validate_notion_token(user_story_id):
    """Validate Notion token for a user story's company"""
    try:
        # Initialize repository first to get user story
        repository = BusinessAutomationRepository()
        
        # Validate that user story exists
        user_story = repository.get_user_story_by_id(user_story_id)
        if not user_story:
            return {"success": False, "error": f"User story with ID {user_story_id} not found"}, 404
        
        from ..repositories.company_repository import CompanyRepository
        
        # Validate token
        validation_result = CompanyRepository.validate_notion_token(user_story.com_id)
        
        return {
            "success": True,
            "user_story_id": user_story_id,
            "com_id": user_story.com_id,
            "validation_result": validation_result
        }, 200
        
    except Exception as e:
        logger.error(f"Error validating Notion token: {e}")
        return {"success": False, "error": f"Failed to validate token: {str(e)}"}, 500

def update_notion_token(user_story_id):
    """Update Notion token for a user story's company - requires new token in request"""
    try:
        from flask import request
        
        # Initialize repository first to get user story
        repository = BusinessAutomationRepository()
        
        # Validate that user story exists
        user_story = repository.get_user_story_by_id(user_story_id)
        if not user_story:
            return {"success": False, "error": f"User story with ID {user_story_id} not found"}, 404
        
        # Get new token from request
        data = request.get_json()
        if not data or not data.get('new_token'):
            return {"success": False, "error": "new_token is required in request body"}, 400
        
        from ..repositories.company_repository import CompanyRepository
        
        # Update token
        updated_account = CompanyRepository.update_notion_token(user_story.com_id, data['new_token'])
        
        if updated_account:
            # Validate the new token
            validation_result = CompanyRepository.validate_notion_token(user_story.com_id)
            
            return {
                "success": True,
                "message": "Token updated successfully",
                "user_story_id": user_story_id,
                "com_id": user_story.com_id,
                "validation_result": validation_result
            }, 200
        else:
            return {"success": False, "error": "Failed to update token - no active Notion account found"}, 404
        
    except Exception as e:
        logger.error(f"Error updating Notion token: {e}")
        return {"success": False, "error": f"Failed to update token: {str(e)}"}, 500