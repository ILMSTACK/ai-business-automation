import os
import time
from typing import Dict, Any, Optional, List
from notion_client import Client
from notion_client.errors import APIResponseError
import logging

logger = logging.getLogger(__name__)

class NotionService:
    def __init__(self, com_id=None):
        """Initialize NotionService with company context"""
        self.com_id = com_id
        self.notion_config = None
        self.client = None
        self.task_database_id = None
        self.testcase_database_id = None
        
        if com_id:
            self._load_company_config()
        else:
            # Fallback to environment variables for backward compatibility
            token = os.getenv("NOTION_TOKEN")
            if token:
                self.client = Client(auth=token)
    
    def _clean_notion_id(self, notion_id: str) -> str:
        """Clean Notion ID to remove URL parameters and format properly"""
        if not notion_id:
            return notion_id
        
        # Remove query parameters (everything after ?)
        clean_id = notion_id.split('?')[0]
        
        # Remove any remaining URL parts and get just the ID
        if '/' in clean_id:
            clean_id = clean_id.split('/')[-1]
        
        # Remove dashes to get clean UUID format
        clean_id = clean_id.replace('-', '')
        
        # Add dashes back in UUID format: 8-4-4-4-12
        if len(clean_id) == 32:
            clean_id = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
        
        return clean_id
    
    def _load_company_config(self):
        """Load Notion configuration from database for company"""
        from ..repositories.company_repository import CompanyRepository
        # from ..services.token_service import TokenService  # TODO: Re-enable when encryption is implemented
        
        try:
            self.notion_config = CompanyRepository.get_notion_config(self.com_id)
            if self.notion_config:
                # Use plain text token directly from database
                token = self.notion_config.notion_token
                # token = TokenService.decode_token(self.notion_config.notion_token)  # TODO: Re-enable when encryption is implemented
                logger.info(f"Using plain text token for company {self.com_id}. Token starts with: {token[:20] if token else 'None'}...")
                
                # Basic token validation (just check if it exists and has reasonable length)
                if not token or len(token) < 20:
                    logger.warning(f"Token appears invalid for company {self.com_id}")
                # if not TokenService.validate_token(token):  # TODO: Re-enable when encryption is implemented
                #     logger.warning(f"Token format appears invalid for company {self.com_id}")
                
                self.client = Client(auth=token)
                # Set database IDs if they exist
                self.task_database_id = self.notion_config.tasks_database_id
                self.testcase_database_id = self.notion_config.testcases_database_id
                
                logger.info(f"NotionService initialized for company {self.com_id}")
            else:
                raise ValueError(f"No active Notion configuration found for company {self.com_id}")
        except Exception as e:
            logger.error(f"Error loading company Notion config: {e}")
            raise

    def _get_enhanced_title(self, item_type, user_story_title, user_story_id):
        """Generate enhanced titles with user story context"""
        return f"{item_type} - {user_story_title} (ID: {user_story_id})"

    def _update_database_ids(self, tasks_db_id=None, testcases_db_id=None):
        """Update database IDs in the notion account"""
        if self.notion_config:
            if tasks_db_id:
                self.notion_config.tasks_database_id = tasks_db_id
                self.task_database_id = tasks_db_id
            if testcases_db_id:
                self.notion_config.testcases_database_id = testcases_db_id
                self.testcase_database_id = testcases_db_id
            
            from ..extensions import db
            db.session.flush()
    
    def _handle_rate_limit(self, func, *args, **kwargs):
        """Handle rate limiting with exponential backoff"""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except APIResponseError as e:
                if e.status == 429:  # Rate limited
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limited, waiting {delay}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error("Max retries exceeded for rate limiting")
                        raise
                else:
                    logger.error(f"Notion API error: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
        
    def create_task_database(self, parent_page_id: str = None) -> str:
        """Create a Notion database for tasks"""
        try:
            properties = {
                "Title": {
                    "title": {}
                },
                "Description": {
                    "rich_text": {}
                },
                "User Story ID": {
                    "number": {}
                },
                "Assignee": {
                    "people": {}
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "Low", "color": "green"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "High", "color": "orange"},
                            {"name": "Critical", "color": "red"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "To Do", "color": "default"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Done", "color": "green"},
                            {"name": "Blocked", "color": "red"}
                        ]
                    }
                },
                "Estimated Hours": {
                    "number": {}
                },
                "Labels": {
                    "multi_select": {
                        "options": []
                    }
                },
                "Created Date": {
                    "created_time": {}
                }
            }
            
            database_data = {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Tasks"}
                    }
                ],
                "properties": properties
            }
            
            # Set parent - either provided page_id or get from company config
            if parent_page_id:
                parent_id = parent_page_id
            elif self.notion_config:
                parent_id = self.notion_config.notion_parent_page_id
            else:
                parent_id = os.getenv("NOTION_PARENT_PAGE_ID")
            
            if not parent_id:
                raise ValueError("Parent page ID is required. Set company Notion config or NOTION_PARENT_PAGE_ID environment variable.")
            
            # Clean the parent ID to ensure proper format
            clean_parent_id = self._clean_notion_id(parent_id)
            database_data["parent"] = {"page_id": clean_parent_id}
            
            response = self._handle_rate_limit(self.client.databases.create, **database_data)
            self.task_database_id = response["id"]
            
            # Update database ID in company config if available
            self._update_database_ids(tasks_db_id=response["id"])
            
            return response["id"]
            
        except APIResponseError as e:
            if "Can't create databases parented by a database" in str(e):
                logger.error("SETUP ERROR: You provided a database ID instead of a page ID. NOTION_PARENT_PAGE_ID must be a PAGE ID, not a database ID. See NOTION_SETUP.txt for details.")
                raise ValueError("Invalid parent: NOTION_PARENT_PAGE_ID must be a page ID, not a database ID. Check NOTION_SETUP.txt for proper setup instructions.")
            else:
                logger.error(f"Notion API error creating task database: {e}")
                raise
        except Exception as e:
            logger.error(f"Error creating task database: {e}")
            raise
    
    def create_testcase_database(self, parent_page_id: str = None) -> str:
        """Create a Notion database for test cases"""
        try:
            properties = {
                "Title": {
                    "title": {}
                },
                "Description": {
                    "rich_text": {}
                },
                "User Story ID": {
                    "number": {}
                },
                "Steps": {
                    "rich_text": {}
                },
                "Expected Result": {
                    "rich_text": {}
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "Low", "color": "green"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "High", "color": "orange"},
                            {"name": "Critical", "color": "red"}
                        ]
                    }
                },
                "Type": {
                    "select": {
                        "options": [
                            {"name": "Functional", "color": "blue"},
                            {"name": "Performance", "color": "purple"},
                            {"name": "Security", "color": "red"},
                            {"name": "Negative", "color": "orange"},
                            {"name": "Validation", "color": "green"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Draft", "color": "default"},
                            {"name": "Active", "color": "blue"},
                            {"name": "Passed", "color": "green"},
                            {"name": "Failed", "color": "red"}
                        ]
                    }
                },
                "Created Date": {
                    "created_time": {}
                }
            }
            
            database_data = {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Test Cases"}
                    }
                ],
                "properties": properties
            }
            
            # Set parent - either provided page_id or get from company config
            if parent_page_id:
                parent_id = parent_page_id
            elif self.notion_config:
                parent_id = self.notion_config.notion_parent_page_id
            else:
                parent_id = os.getenv("NOTION_PARENT_PAGE_ID")
            
            if not parent_id:
                raise ValueError("Parent page ID is required. Set company Notion config or NOTION_PARENT_PAGE_ID environment variable.")
            
            # Clean the parent ID to ensure proper format
            clean_parent_id = self._clean_notion_id(parent_id)
            database_data["parent"] = {"page_id": clean_parent_id}
            
            response = self._handle_rate_limit(self.client.databases.create, **database_data)
            self.testcase_database_id = response["id"]
            
            # Update database ID in company config if available
            self._update_database_ids(testcases_db_id=response["id"])
            
            return response["id"]
            
        except APIResponseError as e:
            if "Can't create databases parented by a database" in str(e):
                logger.error("SETUP ERROR: You provided a database ID instead of a page ID. NOTION_PARENT_PAGE_ID must be a PAGE ID, not a database ID. See NOTION_SETUP.txt for details.")
                raise ValueError("Invalid parent: NOTION_PARENT_PAGE_ID must be a page ID, not a database ID. Check NOTION_SETUP.txt for proper setup instructions.")
            else:
                logger.error(f"Notion API error creating testcase database: {e}")
                raise
        except Exception as e:
            logger.error(f"Error creating testcase database: {e}")
            raise
    
    def _get_or_create_task_database(self) -> str:
        """Get existing task database ID or create new one"""
        if not self.task_database_id:
            if self.notion_config and self.notion_config.tasks_database_id:
                self.task_database_id = self.notion_config.tasks_database_id
            else:
                # Try environment variable as fallback
                self.task_database_id = os.environ.get("NOTION_TASKS_DATABASE_ID")
                if not self.task_database_id:
                    self.task_database_id = self.create_task_database()
        return self.task_database_id
    
    def _get_or_create_testcase_database(self) -> str:
        """Get existing testcase database ID or create new one"""
        if not self.testcase_database_id:
            if self.notion_config and self.notion_config.testcases_database_id:
                self.testcase_database_id = self.notion_config.testcases_database_id
            else:
                # Try environment variable as fallback
                self.testcase_database_id = os.environ.get("NOTION_TESTCASES_DATABASE_ID")
                if not self.testcase_database_id:
                    self.testcase_database_id = self.create_testcase_database()
        return self.testcase_database_id
    
    def push_task_to_notion(self, task_data: Dict[str, Any], user_story_title: str, user_story_id: int) -> str:
        """Create a task entry in the user story task database"""
        try:
            # Get or create unified user story page with both databases
            page_id, tasks_database_id, testcases_database_id = self.get_or_create_user_story_page(user_story_id, user_story_title)
            
            # Prepare properties for the database entry
            properties = {
                "Title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": f"{user_story_id} - Task: {task_data.get('task_title', '')}"}
                        }
                    ]
                },
                "Description": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": task_data.get("task_description", "")}
                        }
                    ]
                },
                "Estimated Hours": {
                    "number": task_data.get("task_estimated_hours", 0)
                }
            }
            
            # Add assignee information if available
            if task_data.get("assignee"):
                assignee = task_data["assignee"]
                properties["Assignee ID"] = {
                    "number": assignee.get("id")
                }
                properties["Assignee Email"] = {
                    "email": assignee.get("email", "")
                }
                # Extract name from email (e.g., john.doe@company.com -> John Doe)
                email = assignee.get("email", "Unknown")
                name = email.split("@")[0].replace(".", " ").replace("_", " ").title() if "@" in email else email
                properties["Assignee Name"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": name}
                        }
                    ]
                }
                if assignee.get("role") and assignee["role"].get("role_name"):
                    properties["Assignee Role"] = {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": assignee["role"]["role_name"]}
                            }
                        ]
                    }
            else:
                # Handle unassigned tasks
                properties["Assignee Name"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Unassigned"}
                        }
                    ]
                }
            
            # Add priority if available
            if task_data.get("priority") and task_data["priority"].get("priority_name"):
                properties["Priority"] = {
                    "select": {"name": task_data["priority"]["priority_name"]}
                }
            
            # Add status if available
            if task_data.get("status") and task_data["status"].get("status_name"):
                # Map database status names to Notion display names
                # Available task statuses: ['To Do', 'In Progress', 'Done', 'Blocked']
                db_to_notion_status_mapping = {
                    "To Do": "To Do",
                    "In Progress": "In Progress",
                    "Done": "Done",
                    "Blocked": "Blocked"
                }
                status_name = db_to_notion_status_mapping.get(task_data["status"]["status_name"], task_data["status"]["status_name"])
                properties["Status"] = {
                    "select": {"name": status_name}
                }
            
            # Add labels if available
            if task_data.get("task_labels"):
                labels = task_data["task_labels"] if isinstance(task_data["task_labels"], list) else task_data["task_labels"].split(",")
                properties["Labels"] = {
                    "multi_select": [{"name": label.strip()} for label in labels if label.strip()]
                }
            
            # Create database entry
            page_data = {
                "parent": {"database_id": tasks_database_id},
                "properties": properties
            }
            
            response = self._handle_rate_limit(self.client.pages.create, **page_data)
            return response["id"]
            
        except Exception as e:
            logger.error(f"Error pushing task to Notion: {e}")
            raise
    
    def push_testcase_to_notion(self, testcase_data: Dict[str, Any], user_story_title: str, user_story_id: int) -> str:
        """Create a test case entry in the user story testcase database"""
        try:
            # Get or create unified user story page with both databases
            page_id, tasks_database_id, testcases_database_id = self.get_or_create_user_story_page(user_story_id, user_story_title)
            
            # Format steps for display in rich text
            steps_text = ""
            if testcase_data.get("test_case_steps"):
                steps = testcase_data["test_case_steps"]
                if isinstance(steps, list):
                    steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                else:
                    steps_text = str(steps)
            
            # Prepare properties for the database entry
            properties = {
                "Title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": f"{user_story_id} - TestCase: {testcase_data.get('test_case_title', '')}"}
                        }
                    ]
                },
                "Description": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": testcase_data.get("test_case_description", "")}
                        }
                    ]
                },
                "Steps": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": steps_text}
                        }
                    ]
                },
                "Expected Result": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": testcase_data.get("test_case_expected_result", "")}
                        }
                    ]
                }
            }
            
            # Add priority if available
            if testcase_data.get("priority") and testcase_data["priority"].get("priority_name"):
                properties["Priority"] = {
                    "select": {"name": testcase_data["priority"]["priority_name"]}
                }
            
            # Add test type if available
            if testcase_data.get("test_type") and testcase_data["test_type"].get("ctgry_name"):
                properties["Type"] = {
                    "select": {"name": testcase_data["test_type"]["ctgry_name"]}
                }
            
            # Add status if available
            if testcase_data.get("status") and testcase_data["status"].get("status_name"):
                # Map database status names to Notion display names
                # After running insert_proper_statuses.sql, available testcase statuses include:
                # ['Draft', 'Active', 'Deprecated', 'PASSED', 'FAILED', 'BLOCKED', 'SKIPPED', 'NOT_EXECUTED', 'IN_PROGRESS']
                db_to_notion_status_mapping = {
                    "Draft": "Draft",
                    "Active": "Active",
                    "Deprecated": "Deprecated",
                    "PASSED": "Passed",
                    "FAILED": "Failed", 
                    "BLOCKED": "Blocked",
                    "SKIPPED": "Skipped",
                    "NOT_EXECUTED": "Not Executed",
                    "IN_PROGRESS": "In Progress"
                }
                status_name = db_to_notion_status_mapping.get(testcase_data["status"]["status_name"], testcase_data["status"]["status_name"])
                properties["Status"] = {
                    "select": {"name": status_name}
                }
            
            # Create database entry
            page_data = {
                "parent": {"database_id": testcases_database_id},
                "properties": properties
            }
            
            response = self._handle_rate_limit(self.client.pages.create, **page_data)
            return response["id"]
            
        except Exception as e:
            logger.error(f"Error pushing test case to Notion: {e}")
            raise
    
    def sync_task_from_notion(self, notion_page_id: str) -> Dict[str, Any]:
        """Get task updates from Notion"""
        try:
            response = self._handle_rate_limit(self.client.pages.retrieve, page_id=notion_page_id)
            
            properties = response.get("properties", {})
            
            # Extract data from Notion properties
            task_data = {}
            
            # Title
            if "Title" in properties and properties["Title"].get("title"):
                task_data["title"] = properties["Title"]["title"][0]["text"]["content"]
            
            # Description
            if "Description" in properties and properties["Description"].get("rich_text"):
                task_data["description"] = properties["Description"]["rich_text"][0]["text"]["content"]
            
            # Status
            if "Status" in properties and properties["Status"].get("select"):
                task_data["status"] = properties["Status"]["select"]["name"]
            
            # Priority
            if "Priority" in properties and properties["Priority"].get("select"):
                task_data["priority"] = properties["Priority"]["select"]["name"]
            
            # Estimated Hours
            if "Estimated Hours" in properties and properties["Estimated Hours"].get("number"):
                task_data["estimated_hours"] = properties["Estimated Hours"]["number"]
            
            # Labels
            if "Labels" in properties and properties["Labels"].get("multi_select"):
                task_data["labels"] = [tag["name"] for tag in properties["Labels"]["multi_select"]]
            
            return task_data
            
        except Exception as e:
            logger.error(f"Error syncing task from Notion: {e}")
            raise
    
    def sync_testcase_from_notion(self, notion_page_id: str) -> Dict[str, Any]:
        """Get test case updates from Notion"""
        try:
            logger.info(f"Attempting to sync testcase from Notion page ID: {notion_page_id}")
            response = self._handle_rate_limit(self.client.pages.retrieve, page_id=notion_page_id)
            logger.info(f"Successfully retrieved testcase from Notion. Response keys: {list(response.keys())}")
            
            properties = response.get("properties", {})
            
            # Extract data from Notion properties
            testcase_data = {}
            
            # Title
            if "Title" in properties and properties["Title"].get("title"):
                testcase_data["title"] = properties["Title"]["title"][0]["text"]["content"]
            
            # Description
            if "Description" in properties and properties["Description"].get("rich_text"):
                testcase_data["description"] = properties["Description"]["rich_text"][0]["text"]["content"]
            
            # Steps
            if "Steps" in properties and properties["Steps"].get("rich_text"):
                testcase_data["steps"] = properties["Steps"]["rich_text"][0]["text"]["content"]
            
            # Expected Result
            if "Expected Result" in properties and properties["Expected Result"].get("rich_text"):
                testcase_data["expected_result"] = properties["Expected Result"]["rich_text"][0]["text"]["content"]
            
            # Status
            if "Status" in properties and properties["Status"].get("select"):
                testcase_data["status"] = properties["Status"]["select"]["name"]
            
            # Priority
            if "Priority" in properties and properties["Priority"].get("select"):
                testcase_data["priority"] = properties["Priority"]["select"]["name"]
            
            # Type
            if "Type" in properties and properties["Type"].get("select"):
                testcase_data["type"] = properties["Type"]["select"]["name"]
            
            return testcase_data
            
        except Exception as e:
            logger.error(f"Error syncing testcase from Notion: {e}")
            raise
    
    def create_user_story_page(self, user_story_title, user_story_id):
        """Create a single user story page with both Tasks and TestCases databases"""
        try:
            parent_page_id = self.notion_config.notion_parent_page_id
            
            # Create the main user story page
            page_data = {
                "parent": {"page_id": parent_page_id},
                "properties": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": f"{user_story_id} - {user_story_title}"}
                        }
                    ]
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"User Story {user_story_id}: {user_story_title}"}
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "Tasks"}
                                }
                            ]
                        }
                    }
                ]
            }
            
            page_response = self._handle_rate_limit(self.client.pages.create, **page_data)
            page_id = page_response["id"]
            
            # Create Tasks database inside this page
            tasks_database_data = {
                "parent": {"page_id": page_id},
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Tasks"}
                    }
                ],
                "properties": {
                    "Title": {
                        "title": {}
                    },
                    "Description": {
                        "rich_text": {}
                    },
                    "Priority": {
                        "select": {
                            "options": [
                                {"name": "Low", "color": "green"},
                                {"name": "Medium", "color": "yellow"},
                                {"name": "High", "color": "orange"},
                                {"name": "Critical", "color": "red"}
                            ]
                        }
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "To Do", "color": "default"},
                                {"name": "In Progress", "color": "blue"},
                                {"name": "Done", "color": "green"},
                                {"name": "Blocked", "color": "red"}
                            ]
                        }
                    },
                    "Estimated Hours": {
                        "number": {}
                    },
                    "Labels": {
                        "multi_select": {
                            "options": []
                        }
                    },
                    "Assignee ID": {
                        "number": {}
                    },
                    "Assignee Email": {
                        "email": {}
                    },
                    "Assignee Name": {
                        "rich_text": {}
                    },
                    "Assignee Role": {
                        "rich_text": {}
                    },
                    "Created Date": {
                        "created_time": {}
                    }
                }
            }
            
            tasks_db_response = self._handle_rate_limit(self.client.databases.create, **tasks_database_data)
            tasks_database_id = tasks_db_response["id"]
            
            # Add TestCases heading and database
            testcases_heading_data = {
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "Test Cases"}
                                }
                            ]
                        }
                    }
                ]
            }
            
            # Add the TestCases heading to the page
            self._handle_rate_limit(
                self.client.blocks.children.append, 
                block_id=page_id, 
                **testcases_heading_data
            )
            
            # Create TestCases database inside this page
            testcases_database_data = {
                "parent": {"page_id": page_id},
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Test Cases"}
                    }
                ],
                "properties": {
                    "Title": {
                        "title": {}
                    },
                    "Description": {
                        "rich_text": {}
                    },
                    "Steps": {
                        "rich_text": {}
                    },
                    "Expected Result": {
                        "rich_text": {}
                    },
                    "Priority": {
                        "select": {
                            "options": [
                                {"name": "Low", "color": "green"},
                                {"name": "Medium", "color": "yellow"},
                                {"name": "High", "color": "orange"},
                                {"name": "Critical", "color": "red"}
                            ]
                        }
                    },
                    "Type": {
                        "select": {
                            "options": [
                                {"name": "Functional", "color": "blue"},
                                {"name": "Performance", "color": "purple"},
                                {"name": "Security", "color": "red"},
                                {"name": "Negative", "color": "orange"},
                                {"name": "Validation", "color": "green"}
                            ]
                        }
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "Draft", "color": "default"},
                                {"name": "Active", "color": "blue"},
                                {"name": "Passed", "color": "green"},
                                {"name": "Failed", "color": "red"}
                            ]
                        }
                    },
                    "Created Date": {
                        "created_time": {}
                    }
                }
            }
            
            testcases_db_response = self._handle_rate_limit(self.client.databases.create, **testcases_database_data)
            testcases_database_id = testcases_db_response["id"]
            
            # Store both database IDs atomically
            from ..repositories.business_automation_repository import BusinessAutomationRepository
            BusinessAutomationRepository.update_user_story_notion_ids(
                user_story_id, 
                page_id=page_id,
                tasks_db_id=tasks_database_id, 
                testcases_db_id=testcases_database_id
            )
            
            return page_id, tasks_database_id, testcases_database_id
            
        except Exception as e:
            logger.error(f"Error creating user story page: {e}")
            raise

    def create_user_story_task_page(self, user_story_title, user_story_id):
        """Create a page for user story tasks with a database inside"""
        try:
            parent_page_id = self.notion_config.notion_parent_page_id
            
            # First, create the page
            page_data = {
                "parent": {"page_id": parent_page_id},
                "properties": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": f"{user_story_id} - Task: {user_story_title}"}
                        }
                    ]
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"Tasks for: {user_story_title}"}
                                }
                            ]
                        }
                    }
                ]
            }
            
            page_response = self._handle_rate_limit(self.client.pages.create, **page_data)
            page_id = page_response["id"]
            
            # Now create a database inside this page
            database_data = {
                "parent": {"page_id": page_id},
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Tasks"}
                    }
                ],
                "properties": {
                    "Title": {
                        "title": {}
                    },
                    "Description": {
                        "rich_text": {}
                    },
                    "Priority": {
                        "select": {
                            "options": [
                                {"name": "Low", "color": "green"},
                                {"name": "Medium", "color": "yellow"},
                                {"name": "High", "color": "orange"},
                                {"name": "Critical", "color": "red"}
                            ]
                        }
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "To Do", "color": "default"},
                                {"name": "In Progress", "color": "blue"},
                                {"name": "Done", "color": "green"},
                                {"name": "Blocked", "color": "red"}
                            ]
                        }
                    },
                    "Estimated Hours": {
                        "number": {}
                    },
                    "Labels": {
                        "multi_select": {
                            "options": []
                        }
                    },
                    "Assignee ID": {
                        "number": {}
                    },
                    "Assignee Email": {
                        "email": {}
                    },
                    "Assignee Name": {
                        "rich_text": {}
                    },
                    "Assignee Role": {
                        "rich_text": {}
                    },
                    "Created Date": {
                        "created_time": {}
                    }
                }
            }
            
            database_response = self._handle_rate_limit(self.client.databases.create, **database_data)
            database_id = database_response["id"]
            
            # Store the database ID
            from ..repositories.business_automation_repository import BusinessAutomationRepository
            BusinessAutomationRepository.update_user_story_task_database_id(user_story_id, database_id)
            
            return page_id, database_id
            
        except Exception as e:
            logger.error(f"Error creating user story task page: {e}")
            raise

    def create_user_story_testcase_page(self, user_story_title, user_story_id):
        """Create a page for user story test cases with a database inside"""
        try:
            parent_page_id = self.notion_config.notion_parent_page_id
            
            # First, create the page
            page_data = {
                "parent": {"page_id": parent_page_id},
                "properties": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": f"{user_story_id} - TestCase: {user_story_title}"}
                        }
                    ]
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"Test Cases for: {user_story_title}"}
                                }
                            ]
                        }
                    }
                ]
            }
            
            page_response = self._handle_rate_limit(self.client.pages.create, **page_data)
            page_id = page_response["id"]
            
            # Now create a database inside this page
            database_data = {
                "parent": {"page_id": page_id},
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Test Cases"}
                    }
                ],
                "properties": {
                    "Title": {
                        "title": {}
                    },
                    "Description": {
                        "rich_text": {}
                    },
                    "Steps": {
                        "rich_text": {}
                    },
                    "Expected Result": {
                        "rich_text": {}
                    },
                    "Priority": {
                        "select": {
                            "options": [
                                {"name": "Low", "color": "green"},
                                {"name": "Medium", "color": "yellow"},
                                {"name": "High", "color": "orange"},
                                {"name": "Critical", "color": "red"}
                            ]
                        }
                    },
                    "Type": {
                        "select": {
                            "options": [
                                {"name": "Functional", "color": "blue"},
                                {"name": "Performance", "color": "purple"},
                                {"name": "Security", "color": "red"},
                                {"name": "Negative", "color": "orange"},
                                {"name": "Validation", "color": "green"}
                            ]
                        }
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "Draft", "color": "default"},
                                {"name": "Active", "color": "blue"},
                                {"name": "Passed", "color": "green"},
                                {"name": "Failed", "color": "red"}
                            ]
                        }
                    },
                    "Created Date": {
                        "created_time": {}
                    }
                }
            }
            
            database_response = self._handle_rate_limit(self.client.databases.create, **database_data)
            database_id = database_response["id"]
            
            # Store the database ID
            from ..repositories.business_automation_repository import BusinessAutomationRepository
            BusinessAutomationRepository.update_user_story_testcase_database_id(user_story_id, database_id)
            
            return page_id, database_id
            
        except Exception as e:
            logger.error(f"Error creating user story testcase page: {e}")
            raise

    def get_or_create_user_story_page(self, user_story_id, user_story_title):
        """Get existing user story page and databases or create new ones"""
        from ..repositories.business_automation_repository import BusinessAutomationRepository
        
        # Check if user story already has page and both databases
        user_story = BusinessAutomationRepository.get_user_story_by_id(user_story_id)
        
        logger.info(f"User story {user_story_id} current state: task_page_id={user_story.notion_task_page_id}, task_db_id={user_story.notion_task_database_id}, testcase_db_id={user_story.notion_testcase_database_id}")
        
        if (user_story.notion_task_page_id and 
            user_story.notion_task_database_id and 
            user_story.notion_testcase_database_id):
            logger.info(f"Reusing existing page for user story {user_story_id}: page={user_story.notion_task_page_id}")
            return (user_story.notion_task_page_id, 
                    user_story.notion_task_database_id, 
                    user_story.notion_testcase_database_id)
        
        # Create new user story page with both databases (updates all IDs atomically)
        logger.info(f"Creating new user story page with both databases for user story {user_story_id}")
        page_id, tasks_db_id, testcases_db_id = self.create_user_story_page(user_story_title, user_story_id)
        
        logger.info(f"Created page {page_id} with tasks_db={tasks_db_id}, testcases_db={testcases_db_id}")
        logger.info(f"All Notion IDs updated atomically for user story {user_story_id}")
        
        return page_id, tasks_db_id, testcases_db_id

    def get_or_create_user_story_task_page(self, user_story_id, user_story_title):
        """Get existing user story page and task database (for backwards compatibility)"""
        page_id, tasks_db_id, testcases_db_id = self.get_or_create_user_story_page(user_story_id, user_story_title)
        return page_id, tasks_db_id

    def get_or_create_user_story_testcase_page(self, user_story_id, user_story_title):
        """Get existing user story page and testcase database (for backwards compatibility)"""
        page_id, tasks_db_id, testcases_db_id = self.get_or_create_user_story_page(user_story_id, user_story_title)
        return page_id, testcases_db_id

    def get_notion_page_url(self, page_id: str) -> str:
        """Get the URL for a Notion page"""
        return f"https://notion.so/{page_id.replace('-', '')}"