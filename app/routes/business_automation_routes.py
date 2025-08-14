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
    @api.marshal_list_with(testcase_model)
    def get(self, user_story_id):
        """Get generated test cases by user story ID"""
        return get_testcases_by_story_id(user_story_id)

# ========================================
# TASK ENDPOINTS
# ========================================

@api.route('/tasks/<int:user_story_id>')
class TaskRetrieval(Resource):
    @api.doc('get_tasks')
    @api.marshal_list_with(task_model)
    def get(self, user_story_id):
        """Get generated tasks by user story ID"""
        return get_tasks_by_story_id(user_story_id)

# ========================================
# ANALYTICS & SEARCH 
# ========================================

@api.route('/history')
class GenerationHistory(Resource):
    @api.doc('get_generation_history')
    @api.marshal_list_with(history_model)
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