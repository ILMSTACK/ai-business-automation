from flask import request
from ..services.business_automation_service import BusinessAutomationService


def create_user_story_and_generate():
    """Create user story and automatically generate testcases + tasks"""
    try:
        data = request.get_json()
        if not data or 'user_story' not in data or 'title' not in data:
            return {
                "success": False,
                "error": "user_story and title are required"
            }, 400

        user_story = data['user_story']
        title = data['title']

        # Basic validation
        if len(user_story) < 10:
            return {
                "success": False,
                "error": "user_story must be at least 10 characters long"
            }, 400

        if len(title) < 3:
            return {
                "success": False,
                "error": "title must be at least 3 characters long"
            }, 400

        # Call service to create user story and generate content
        result = BusinessAutomationService.create_user_story_and_generate(user_story, title)

        return {
            "success": True,
            "user_story_id": result['user_story_id'],
            "data": result['data']
        }, 201

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500


def get_testcases_by_story_id(user_story_id):
    """Get generated test cases by user story ID"""
    try:
        testcases = BusinessAutomationService.get_testcases_by_story_id(user_story_id)

        if testcases is None:
            return {
                "success": False,
                "error": "No testcases found for this user story ID"
            }, 404

        return {
            "success": True,
            "data": testcases,
            "user_story_id": user_story_id
        }, 200

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500


def get_tasks_by_story_id(user_story_id):
    """Get generated tasks by user story ID"""
    try:
        tasks = BusinessAutomationService.get_tasks_by_story_id(user_story_id)

        if tasks is None:
            return {
                "success": False,
                "error": "No tasks found for this user story ID"
            }, 404

        return {
            "success": True,
            "data": tasks,
            "user_story_id": user_story_id
        }, 200

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500


def get_generation_history():
    """Get history of all generations"""
    try:
        history = BusinessAutomationService.get_generation_history()
        return {
            "success": True,
            "data": history
        }, 200

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500


def get_user_story_by_id(user_story_id):
    """Get user story details by ID"""
    try:
        user_story = BusinessAutomationService.get_user_story_by_id(user_story_id)
        if not user_story:
            return {
                "success": False,
                "error": "User story not found"
            }, 404

        return {
            "success": True,
            "data": user_story
        }, 200

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500


def get_dashboard_statistics():
    """Get dashboard statistics"""
    try:
        stats = BusinessAutomationService.get_dashboard_statistics()
        return {
            "success": True,
            "data": stats
        }, 200

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500


def search_user_stories():
    """Search user stories"""
    try:
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return {
                "success": False,
                "error": "Search term 'q' is required"
            }, 400

        if len(search_term) < 2:
            return {
                "success": False,
                "error": "Search term must be at least 2 characters long"
            }, 400

        results = BusinessAutomationService.search_user_stories(search_term)
        return {
            "success": True,
            "data": results,
            "search_term": search_term
        }, 200

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500