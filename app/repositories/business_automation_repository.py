from sqlalchemy import func, desc
from datetime import datetime, timedelta, UTC
import logging
from ..models.dt_user_story import DtUserStory
from ..models.dt_test_case import DtTestCase
from ..models.dt_task import DtTask
from ..models.dt_generation_log import DtGenerationLog
from ..models.lt_priority import LtPriority
from ..models.lt_general_status import LtGeneralStatus
from ..models.lt_category_ctgry import LtCategoryCtgry
from ..models.lt_role import LtRole
from ..models.user import User
from ..extensions import db

logger = logging.getLogger(__name__)


class BusinessAutomationRepository:
    """Repository for all database queries and complex operations"""

    # ========================================
    # LOOKUP TABLE HELPERS
    # ========================================

    @staticmethod
    def get_priority_id_by_code(priority_code):
        """Get priority ID by code"""
        priority = LtPriority.query.filter_by(priority_code=priority_code.upper()).first()
        return priority.priority_id if priority else None

    @staticmethod
    def get_status_id_by_code(status_code, category=None):
        """Get status ID by code and optional category"""
        query = LtGeneralStatus.query.filter_by(status_code=status_code.upper())
        if category:
            query = query.filter_by(status_category=category)
        status = query.first()
        return status.status_id if status else None

    @staticmethod
    def get_category_id_by_code(category_code):
        """Get category ID by code"""
        category = LtCategoryCtgry.query.filter_by(ctgry_code=category_code.upper()).first()
        return category.ctgry_id if category else None

    @staticmethod
    def get_user_id_by_email(email):
        """Get user ID by email"""
        user = User.query.filter_by(email=email).first()
        return user.id if user else None

    @staticmethod
    def get_all_priorities():
        """Get all active priorities"""
        return LtPriority.query.filter_by(priority_is_active=True).order_by(LtPriority.priority_level).all()

    @staticmethod
    def get_all_statuses_by_category(category):
        """Get all active statuses for a specific category"""
        return LtGeneralStatus.query.filter_by(
            status_category=category,
            status_is_active=True
        ).all()

    @staticmethod
    def get_all_categories():
        """Get all active categories"""
        return LtCategoryCtgry.query.filter_by(ctgry_is_active=True).all()

    # ========================================
    # USER STORY OPERATIONS
    # ========================================

    @staticmethod
    def create_user_story(title, content):
        """Create a new user story"""
        user_story = DtUserStory(
            user_story_title=title,
            user_story_content=content
        )
        db.session.add(user_story)
        db.session.flush()  # Get ID without committing
        return user_story

    @staticmethod
    def get_user_story_by_id(user_story_id):
        """Get user story by ID"""
        return DtUserStory.query.filter_by(user_story_id=user_story_id).first()

    @staticmethod
    def get_all_user_stories():
        """Get all user stories ordered by creation date"""
        return DtUserStory.query.order_by(desc(DtUserStory.user_story_created_at)).all()

    # ========================================
    # TEST CASE OPERATIONS
    # ========================================

    @staticmethod
    def create_testcase(user_story_id, title, description, steps, expected_result, priority_code, test_type_code):
        """Create a new test case using lookup codes"""
        # Get IDs from lookup tables
        priority_id = BusinessAutomationRepository.get_priority_id_by_code(priority_code)
        type_id = BusinessAutomationRepository.get_category_id_by_code(test_type_code)
        status_id = BusinessAutomationRepository.get_status_id_by_code('DRAFT', 'testcase')  # Default to DRAFT

        testcase = DtTestCase(
            user_story_id=user_story_id,
            test_case_title=title,
            test_case_description=description,
            test_case_steps=steps,
            test_case_expected_result=expected_result,
            test_case_priority_id=priority_id,
            test_case_type_id=type_id,
            test_case_status_id=status_id
        )
        db.session.add(testcase)
        return testcase

    @staticmethod
    def get_testcases_by_story_id(user_story_id):
        """Get all test cases for a specific user story with relationships"""
        return DtTestCase.query.filter_by(user_story_id=user_story_id)\
            .options(
                db.joinedload(DtTestCase.priority),
                db.joinedload(DtTestCase.test_type),
                db.joinedload(DtTestCase.status)
            ).all()

    @staticmethod
    def count_testcases_by_story_id(user_story_id):
        """Count test cases for a specific user story"""
        return DtTestCase.query.filter_by(user_story_id=user_story_id).count()

    # ========================================
    # TASK OPERATIONS
    # ========================================

    @staticmethod
    def create_task(user_story_id, title, description, assignee_email, priority_code, estimated_hours, labels):
        """Create a new task using lookup codes"""
        # Get IDs from lookup tables
        priority_id = BusinessAutomationRepository.get_priority_id_by_code(priority_code)
        status_id = BusinessAutomationRepository.get_status_id_by_code('TODO', 'task')  # Default to TODO
        assignee_user_id = BusinessAutomationRepository.get_user_id_by_email(assignee_email) if assignee_email != 'Unassigned' else None

        task = DtTask(
            user_story_id=user_story_id,
            task_title=title,
            task_description=description,
            task_assignee_user_id=assignee_user_id,
            task_priority_id=priority_id,
            task_status_id=status_id,
            task_estimated_hours=estimated_hours,
            task_labels=labels
        )
        db.session.add(task)
        return task

    @staticmethod
    def get_all_active_users():
        """Get all active users with VARCHAR roles"""
        users = User.query.all()
        return [
            {
                'email': user.email,
                'role': {'role_name': user.role.role_name or 'Developer'}
            }
            for user in users
        ]

    @staticmethod
    def get_tasks_by_story_id(user_story_id):
        """Get all tasks for a specific user story with relationships"""
        return DtTask.query.filter_by(user_story_id=user_story_id)\
            .options(
                db.joinedload(DtTask.assignee),
                db.joinedload(DtTask.priority),
                db.joinedload(DtTask.status)
            ).all()

    @staticmethod
    def count_tasks_by_story_id(user_story_id):
        """Count tasks for a specific user story"""
        return DtTask.query.filter_by(user_story_id=user_story_id).count()

    # ========================================
    # GENERATION LOG OPERATIONS
    # ========================================

    @staticmethod
    def create_generation_log(user_story_id, log_type_code, status_code, items_generated, processing_time=None, error_message=None):
        """Create a generation log entry using lookup codes"""
        type_id = BusinessAutomationRepository.get_category_id_by_code(log_type_code)
        status_id = BusinessAutomationRepository.get_status_id_by_code(status_code, 'generation')

        generation_log = DtGenerationLog(
            user_story_id=user_story_id,
            generation_log_type_id=type_id,
            generation_log_status_id=status_id,
            generation_log_items_generated=items_generated,
            generation_log_processing_time=processing_time,
            generation_log_error_message=error_message
        )
        db.session.add(generation_log)
        return generation_log

    # ========================================
    # COMPLEX QUERIES AND JOINS
    # ========================================

    @staticmethod
    def get_user_story_with_counts(user_story_id):
        """Get user story with test case and task counts"""
        result = db.session.query(
            DtUserStory,
            func.count(DtTestCase.test_case_id.distinct()).label('testcase_count'),
            func.count(DtTask.task_id.distinct()).label('task_count')
        ).outerjoin(
            DtTestCase, DtUserStory.user_story_id == DtTestCase.user_story_id
        ).outerjoin(
            DtTask, DtUserStory.user_story_id == DtTask.user_story_id
        ).filter(
            DtUserStory.user_story_id == user_story_id
        ).group_by(DtUserStory.user_story_id).first()

        if result:
            user_story, testcase_count, task_count = result
            return {
                'user_story': user_story,
                'testcase_count': testcase_count,
                'task_count': task_count
            }
        return None

    @staticmethod
    def get_generation_history_with_counts():
        """Get all user stories with their generation counts"""
        results = db.session.query(
            DtUserStory.user_story_id,
            DtUserStory.user_story_title,
            DtUserStory.user_story_created_at,
            func.count(DtTestCase.test_case_id.distinct()).label('testcase_count'),
            func.count(DtTask.task_id.distinct()).label('task_count')
        ).outerjoin(
            DtTestCase, DtUserStory.user_story_id == DtTestCase.user_story_id
        ).outerjoin(
            DtTask, DtUserStory.user_story_id == DtTask.user_story_id
        ).group_by(
            DtUserStory.user_story_id,
            DtUserStory.user_story_title,
            DtUserStory.user_story_created_at
        ).order_by(desc(DtUserStory.user_story_created_at)).all()

        history = []
        for result in results:
            history.append({
                'user_story_id': result.user_story_id,
                'user_story_title': result.user_story_title,
                'user_story_created_at': result.user_story_created_at.isoformat() if result.user_story_created_at else None,
                'testcase_count': result.testcase_count,
                'task_count': result.task_count
            })

        return history

    @staticmethod
    def get_dashboard_statistics():
        """Get comprehensive dashboard statistics"""
        # Total counts
        total_user_stories = db.session.query(func.count(DtUserStory.user_story_id)).scalar()
        total_testcases = db.session.query(func.count(DtTestCase.test_case_id)).scalar()
        total_tasks = db.session.query(func.count(DtTask.task_id)).scalar()
        total_generations = db.session.query(func.count(DtGenerationLog.generation_log_id)).scalar()

        # Recent counts (last 30 days)
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        recent_user_stories = db.session.query(func.count(DtUserStory.user_story_id)) \
            .filter(DtUserStory.user_story_created_at >= thirty_days_ago).scalar()

        # Success rate - need to check by status code now
        success_status = LtGeneralStatus.query.filter_by(status_code='SUCCESS', status_category='generation').first()
        if success_status:
            successful_generations = db.session.query(func.count(DtGenerationLog.generation_log_id)) \
                .filter(DtGenerationLog.generation_log_status_id == success_status.status_id).scalar()
        else:
            successful_generations = 0

        success_rate = (successful_generations / total_generations * 100) if total_generations > 0 else 0

        return {
            'total_user_stories': total_user_stories,
            'total_testcases': total_testcases,
            'total_tasks': total_tasks,
            'total_generations': total_generations,
            'recent_user_stories': recent_user_stories,
            'success_rate': round(success_rate, 2)
        }

    @staticmethod
    def search_user_stories(search_term):
        """Search user stories by title or content"""
        search_pattern = f"%{search_term}%"
        return DtUserStory.query.filter(
            db.or_(
                DtUserStory.user_story_title.ilike(search_pattern),
                DtUserStory.user_story_content.ilike(search_pattern)
            )
        ).order_by(desc(DtUserStory.user_story_created_at)).all()

    # ========================================
    # DATABASE OPERATIONS
    # ========================================

    @staticmethod
    def commit_transaction():
        """Commit the current transaction"""
        db.session.commit()

    @staticmethod
    def rollback_transaction():
        """Rollback the current transaction"""
        db.session.rollback()

    @staticmethod
    def flush_session():
        """Flush the session to get IDs without committing"""
        db.session.flush()

    # ========================================
    # NOTION INTEGRATION METHODS
    # ========================================

    @staticmethod
    def update_task_notion_id(task_id, notion_page_id):
        """Update a task with its Notion page ID"""
        task = DtTask.query.filter_by(task_id=task_id).first()
        if task:
            task.notion_page_id = notion_page_id
            db.session.commit()
        return task

    @staticmethod
    def update_testcase_notion_id(test_case_id, notion_page_id):
        """Update a test case with its Notion page ID"""
        test_case = DtTestCase.query.filter_by(test_case_id=test_case_id).first()
        if test_case:
            test_case.notion_page_id = notion_page_id
            db.session.commit()
        return test_case

    @staticmethod
    def get_task_by_id(task_id):
        """Get task by ID with relationships"""
        return DtTask.query.filter_by(task_id=task_id)\
            .options(
                db.joinedload(DtTask.assignee),
                db.joinedload(DtTask.priority),
                db.joinedload(DtTask.status)
            ).first()

    @staticmethod
    def get_testcase_by_id(test_case_id):
        """Get test case by ID with relationships"""
        return DtTestCase.query.filter_by(test_case_id=test_case_id)\
            .options(
                db.joinedload(DtTestCase.priority),
                db.joinedload(DtTestCase.test_type),
                db.joinedload(DtTestCase.status)
            ).first()

    @staticmethod
    def get_tasks_by_user_story_id(user_story_id):
        """Get all tasks for a specific user story with relationships"""
        return DtTask.query.filter_by(user_story_id=user_story_id)\
            .options(
                db.joinedload(DtTask.assignee),
                db.joinedload(DtTask.priority),
                db.joinedload(DtTask.status)
            ).all()

    @staticmethod
    def get_testcases_by_user_story_id(user_story_id):
        """Get all test cases for a specific user story with relationships"""
        return DtTestCase.query.filter_by(user_story_id=user_story_id)\
            .options(
                db.joinedload(DtTestCase.priority),
                db.joinedload(DtTestCase.test_type),
                db.joinedload(DtTestCase.status)
            ).all()

    @staticmethod
    def update_user_story_task_page_id(user_story_id, notion_page_id):
        """Update user story with its Notion task page ID"""
        user_story = DtUserStory.query.filter_by(user_story_id=user_story_id).first()
        if user_story:
            user_story.notion_task_page_id = notion_page_id
            db.session.commit()
        return user_story

    @staticmethod
    def update_user_story_testcase_page_id(user_story_id, notion_page_id):
        """Update user story with its Notion testcase page ID"""
        user_story = DtUserStory.query.filter_by(user_story_id=user_story_id).first()
        if user_story:
            user_story.notion_testcase_page_id = notion_page_id
            db.session.commit()
        return user_story

    @staticmethod
    def update_user_story_task_database_id(user_story_id, notion_database_id):
        """Update user story with its Notion task database ID"""
        user_story = DtUserStory.query.filter_by(user_story_id=user_story_id).first()
        if user_story:
            user_story.notion_task_database_id = notion_database_id
            db.session.commit()
        return user_story

    @staticmethod
    def update_user_story_testcase_database_id(user_story_id, notion_database_id):
        """Update user story with its Notion testcase database ID"""
        user_story = DtUserStory.query.filter_by(user_story_id=user_story_id).first()
        if user_story:
            user_story.notion_testcase_database_id = notion_database_id
            db.session.commit()
        return user_story

    @staticmethod
    def update_user_story_notion_ids(user_story_id, page_id=None, tasks_db_id=None, testcases_db_id=None):
        """Update user story with all Notion IDs in a single transaction"""
        user_story = DtUserStory.query.filter_by(user_story_id=user_story_id).first()
        if user_story:
            if page_id is not None:
                user_story.notion_task_page_id = page_id
                user_story.notion_testcase_page_id = page_id  # Same page for both
            if tasks_db_id is not None:
                user_story.notion_task_database_id = tasks_db_id
            if testcases_db_id is not None:
                user_story.notion_testcase_database_id = testcases_db_id
            db.session.commit()
        return user_story

    @staticmethod
    def update_task_from_notion_sync(task_id, notion_data):
        """Update task with synced data from Notion"""
        task = DtTask.query.filter_by(task_id=task_id).first()
        if task:
            # Update fields that can be synced from Notion
            if 'title' in notion_data:
                task.task_title = notion_data['title']
            if 'description' in notion_data:
                task.task_description = notion_data['description']
            if 'estimated_hours' in notion_data:
                task.task_estimated_hours = notion_data['estimated_hours']
            if 'labels' in notion_data and isinstance(notion_data['labels'], list):
                task.task_labels = ','.join(notion_data['labels'])
            
            # Update status if we can map it
            if 'status' in notion_data:
                from ..models.lt_general_status import LtGeneralStatus
                
                # Map Notion display names to actual database status names
                # Available task statuses: ['To Do', 'In Progress', 'Done', 'Blocked']
                notion_to_db_status_mapping = {
                    "Draft": "To Do",  # Map Draft to closest equivalent
                    "To Do": "To Do",
                    "In Progress": "In Progress", 
                    "Done": "Done",
                    "Completed": "Done",  # Map Completed to Done
                    "Blocked": "Blocked",
                    "Active": "In Progress"  # Map Active to In Progress
                }
                
                db_status_name = notion_to_db_status_mapping.get(notion_data['status'], "To Do")  # Default to "To Do"
                logger.info(f"Looking for task status: '{db_status_name}' (mapped from Notion: '{notion_data['status']}')")
                
                status = LtGeneralStatus.query.filter_by(
                    status_name=db_status_name,
                    status_category='task'
                ).first()
                
                if status:
                    logger.info(f"Found matching task status: {status.status_name} (ID: {status.status_id})")
                    task.task_status_id = status.status_id
                else:
                    logger.warning(f"No matching task status found for '{db_status_name}' in category 'task'")
                    # If no task statuses found, debug what's actually available
                    available_statuses = LtGeneralStatus.query.filter_by(status_category='task').all()
                    if not available_statuses:
                        all_statuses = LtGeneralStatus.query.all()
                        categories = list(set([s.status_category for s in all_statuses if s.status_category]))
                        logger.warning(f"No task statuses found. Available categories: {categories}")
                    else:
                        logger.warning(f"Available task statuses: {[s.status_name for s in available_statuses]}")
            
            # Update priority if we can map it
            if 'priority' in notion_data:
                from ..models.lt_priority import LtPriority
                priority = LtPriority.query.filter_by(priority_name=notion_data['priority']).first()
                if priority:
                    task.task_priority_id = priority.priority_id
            
            # Update sync status
            from datetime import datetime, UTC
            task.notion_synced_at = datetime.now(UTC)
            task.notion_sync_status = 'synced'
            
            db.session.commit()
        return task

    @staticmethod
    def update_testcase_from_notion_sync(test_case_id, notion_data):
        """Update test case with synced data from Notion"""
        test_case = DtTestCase.query.filter_by(test_case_id=test_case_id).first()
        if test_case:
            # Update fields that can be synced from Notion
            if 'title' in notion_data:
                test_case.test_case_title = notion_data['title']
            if 'description' in notion_data:
                test_case.test_case_description = notion_data['description']
            if 'steps' in notion_data:
                test_case.test_case_steps = notion_data['steps']
            if 'expected_result' in notion_data:
                test_case.test_case_expected_result = notion_data['expected_result']
            
            # Update status if we can map it
            if 'status' in notion_data:
                from ..models.lt_general_status import LtGeneralStatus
                
                # Map Notion display names to proper database status names
                # After running insert_proper_statuses.sql, available testcase statuses include:
                # ['Draft', 'Active', 'Deprecated', 'PASSED', 'FAILED', 'BLOCKED', 'SKIPPED', 'NOT_EXECUTED', 'IN_PROGRESS']
                notion_to_db_status_mapping = {
                    "Draft": "Draft",
                    "Active": "Active", 
                    "Passed": "PASSED",  # Use proper PASSED status
                    "Failed": "FAILED",  # Use proper FAILED status
                    "Blocked": "BLOCKED",  # Use proper BLOCKED status
                    "Skipped": "SKIPPED",
                    "Not Executed": "NOT_EXECUTED",
                    "In Progress": "IN_PROGRESS",
                    "Deprecated": "Deprecated"
                }
                
                db_status_name = notion_to_db_status_mapping.get(notion_data['status'], "Draft")  # Default to "Draft"
                logger.info(f"Looking for test case status: '{db_status_name}' (mapped from Notion: '{notion_data['status']}')")
                
                status = LtGeneralStatus.query.filter_by(
                    status_name=db_status_name,
                    status_category='testcase'  # Fixed: use 'testcase' not 'test_case'
                ).first()
                
                if status:
                    logger.info(f"Found matching test case status: {status.status_name} (ID: {status.status_id})")
                    test_case.test_case_status_id = status.status_id
                else:
                    logger.warning(f"No matching test case status found for '{db_status_name}' in category 'test_case'")
                    # Debug: Check what categories and statuses actually exist
                    all_statuses = LtGeneralStatus.query.all()
                    categories = list(set([s.status_category for s in all_statuses if s.status_category]))
                    logger.warning(f"All available status categories: {categories}")
                    
                    # Show statuses for each category
                    for category in categories:
                        cat_statuses = LtGeneralStatus.query.filter_by(status_category=category).all()
                        logger.warning(f"Statuses in category '{category}': {[s.status_name for s in cat_statuses]}")
                    
                    # Also try without category filter
                    statuses_without_category = LtGeneralStatus.query.filter(
                        (LtGeneralStatus.status_category == None) | (LtGeneralStatus.status_category == '')
                    ).all()
                    if statuses_without_category:
                        logger.warning(f"Statuses without category: {[s.status_name for s in statuses_without_category]}")
            
            # Update priority if we can map it
            if 'priority' in notion_data:
                from ..models.lt_priority import LtPriority
                priority = LtPriority.query.filter_by(priority_name=notion_data['priority']).first()
                if priority:
                    test_case.test_case_priority_id = priority.priority_id
            
            # Update type if we can map it
            if 'type' in notion_data:
                from ..models.lt_category_ctgry import LtCategoryCtgry
                test_type = LtCategoryCtgry.query.filter_by(ctgry_name=notion_data['type']).first()
                if test_type:
                    test_case.test_case_type_id = test_type.ctgry_id
            
            # Update sync status
            from datetime import datetime, UTC
            test_case.notion_synced_at = datetime.now(UTC)
            test_case.notion_sync_status = 'synced'
            
            db.session.commit()
        return test_case