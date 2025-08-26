from flask_restx import Namespace, Resource, fields
from ..controllers.business_automation_controller import (
    create_user_story_and_generate,
    get_testcases_by_story_id,
    get_tasks_by_story_id,
    get_generation_history,
    get_user_story_by_id,
    get_dashboard_statistics,
    search_user_stories
)
from ..controllers.notion_controller import (
    create_notion_task,
    create_notion_testcase,
    sync_notion_task,
    sync_notion_testcase,
    create_notion_all_tasks,
    create_notion_all_testcases,
    validate_notion_token,
    update_notion_token
)

# Create namespace for Swagger documentation
api = Namespace('business-automation', description='Business automation operations')

# Swagger Models
user_story_request = api.model('UserStoryRequest', {
    'user_story': fields.String(required=True, description='User story content', 
                               example='As a user, I want to login so that I can access my account'),
    'title': fields.String(required=True, description='User story title', 
                          example='User Login Feature')
})

testcase_model = api.model('TestCase', {
    'test_case_id': fields.Integer(description='Test case ID'),
    'test_case_title': fields.String(description='Test case title'),
    'test_case_description': fields.String(description='Test case description'),
    'test_case_steps': fields.List(fields.String, description='Test steps'),
    'test_case_expected_result': fields.String(description='Expected result'),
    'test_case_priority': fields.String(description='Priority'),
    'test_case_type': fields.String(description='Test type'),
    'test_case_status': fields.String(description='Test status'),
    'test_case_created_at': fields.DateTime(description='Creation date')
})

task_model = api.model('Task', {
    'task_id': fields.Integer(description='Task ID'),
    'task_title': fields.String(description='Task title'),
    'task_description': fields.String(description='Task description'),
    'task_assignee': fields.String(description='Assignee'),
    'task_priority': fields.String(description='Priority'),
    'task_status': fields.String(description='Status'),
    'task_estimated_hours': fields.Float(description='Estimated hours'),
    'task_labels': fields.List(fields.String, description='Labels'),
    'task_created_at': fields.DateTime(description='Creation date')
})

create_response = api.model('CreateResponse', {
    'success': fields.Boolean(description='Success status'),
    'user_story_id': fields.Integer(description='Created user story ID'),
    'data': fields.Raw(description='Generated content')
})

history_model = api.model('GenerationHistory', {
    'user_story_id': fields.Integer(description='User story ID'),
    'user_story_title': fields.String(description='User story title'),
    'testcase_count': fields.Integer(description='Number of test cases'),
    'task_count': fields.Integer(description='Number of tasks'),
    'user_story_created_at': fields.DateTime(description='Creation date')
})

dashboard_stats_model = api.model('DashboardStatistics', {
    'total_user_stories': fields.Integer(description='Total number of user stories'),
    'total_testcases': fields.Integer(description='Total number of test cases'),
    'total_tasks': fields.Integer(description='Total number of tasks'),
    'total_generations': fields.Integer(description='Total number of generations'),
    'recent_user_stories': fields.Integer(description='Recent user stories (last 30 days)'),
    'success_rate': fields.Float(description='Generation success rate percentage')
})

# Notion Integration Models
notion_response_model = api.model('NotionResponse', {
    'message': fields.String(description='Response message'),
    'task_id': fields.Integer(description='Task ID (for task operations)'),
    'test_case_id': fields.Integer(description='Test case ID (for test case operations)'),
    'notion_page_id': fields.String(description='Notion page ID'),
    'notion_url': fields.String(description='Notion page URL')
})

bulk_notion_response_model = api.model('BulkNotionResponse', {
    'message': fields.String(description='Response message'),
    'user_story_id': fields.Integer(description='User story ID'),
    'total_tasks': fields.Integer(description='Total number of tasks processed'),
    'total_test_cases': fields.Integer(description='Total number of test cases processed'),
    'success_count': fields.Integer(description='Number of successful operations'),
    'error_count': fields.Integer(description='Number of failed operations'),
    'results': fields.List(fields.Raw, description='Detailed results for each item')
})

sync_response_model = api.model('SyncResponse', {
    'message': fields.String(description='Response message'),
    'task_id': fields.Integer(description='Task ID (for task operations)'),
    'test_case_id': fields.Integer(description='Test case ID (for test case operations)'),
    'notion_page_id': fields.String(description='Notion page ID'),
    'synced_data': fields.Raw(description='Data synced from Notion')
})

# ========================================
# MAIN WORKFLOW ENDPOINTS
# ========================================
@api.route('/create')
class UserStoryCreate(Resource):
    @api.doc('create_user_story_and_generate')
    @api.expect(user_story_request)
    @api.marshal_with(create_response, code=201)
    def post(self):
        """Create user story and automatically generate testcases + tasks"""
        return create_user_story_and_generate()

@api.route('/user-story/<int:user_story_id>')
class UserStoryDetails(Resource):
    @api.doc('get_user_story')
    def get(self, user_story_id):
        """Get user story details by ID"""
        return get_user_story_by_id(user_story_id)

# ========================================
# TESTCASE ENDPOINTS
# ========================================

@api.route('/testcases/<int:user_story_id>')
class TestCaseRetrieval(Resource):
    @api.doc('get_testcases')
    def get(self, user_story_id):
        """Get generated test cases by user story ID"""
        return get_testcases_by_story_id(user_story_id)

# ========================================
# TASK ENDPOINTS
# ========================================

@api.route('/tasks/<int:user_story_id>')
class TaskRetrieval(Resource):
    @api.doc('get_tasks')
    def get(self, user_story_id):
        """Get generated tasks by user story ID"""
        return get_tasks_by_story_id(user_story_id)

# ========================================
# ANALYTICS & SEARCH 
# ========================================

@api.route('/history')
class GenerationHistory(Resource):
    @api.doc('get_generation_history')
    def get(self):
        """Get history of all """
        return get_generation_history()


@api.route('/search')
class SearchUserStories(Resource):
    @api.doc('search_user_stories')
    @api.param('q', 'Search term', required=True, type='string')
    def get(self):
        """Search user stories by title or content"""
        return search_user_stories()

# ========================================
# NOTION INTEGRATION ENDPOINTS
# ========================================

@api.route('/notion/createNotionTask/<int:user_story_id>/<int:task_id>')
class CreateNotionTask(Resource):
    @api.doc('create_notion_task')
    @api.marshal_with(notion_response_model, code=201)
    def post(self, user_story_id, task_id):
        """Create individual task in Notion"""
        return create_notion_task(user_story_id, task_id)

@api.route('/notion/createNotionTestCase/<int:user_story_id>/<int:test_case_id>')
class CreateNotionTestCase(Resource):
    @api.doc('create_notion_testcase')
    @api.marshal_with(notion_response_model, code=201)
    def post(self, user_story_id, test_case_id):
        """Create individual test case in Notion"""
        return create_notion_testcase(user_story_id, test_case_id)

@api.route('/notion/syncNotionTask/<int:user_story_id>/<int:task_id>')
class SyncNotionTask(Resource):
    @api.doc('sync_notion_task')
    @api.marshal_with(sync_response_model, code=200)
    def post(self, user_story_id, task_id):
        """Sync task updates from Notion to local database"""
        return sync_notion_task(user_story_id, task_id)

@api.route('/notion/syncNotionTestCase/<int:user_story_id>/<int:test_case_id>')
class SyncNotionTestCase(Resource):
    @api.doc('sync_notion_testcase')
    @api.marshal_with(sync_response_model, code=200)
    def post(self, user_story_id, test_case_id):
        """Sync test case updates from Notion to local database"""
        return sync_notion_testcase(user_story_id, test_case_id)

@api.route('/notion/createNotionAllTasks/<int:user_story_id>')
class CreateNotionAllTasks(Resource):
    @api.doc('create_notion_all_tasks')
    @api.marshal_with(bulk_notion_response_model, code=200)
    def post(self, user_story_id):
        """Create all tasks for a user story in Notion"""
        return create_notion_all_tasks(user_story_id)

@api.route('/notion/createNotionAllTestCases/<int:user_story_id>')
class CreateNotionAllTestCases(Resource):
    @api.doc('create_notion_all_testcases')
    @api.marshal_with(bulk_notion_response_model, code=200)
    def post(self, user_story_id):
        """Create all test cases for a user story in Notion"""
        return create_notion_all_testcases(user_story_id)

@api.route('/notion/validateToken/<int:user_story_id>')
class ValidateNotionToken(Resource):
    @api.doc('validate_notion_token')
    def get(self, user_story_id):
        """Validate Notion token for a user story's company"""
        return validate_notion_token(user_story_id)

@api.route('/notion/updateToken/<int:user_story_id>')
class UpdateNotionToken(Resource):
    @api.doc('update_notion_token')
    @api.expect(api.model('UpdateTokenRequest', {
        'new_token': fields.String(required=True, description='New Notion API token')
    }))
    def post(self, user_story_id):
        """Update Notion token for a user story's company"""
        return update_notion_token(user_story_id)