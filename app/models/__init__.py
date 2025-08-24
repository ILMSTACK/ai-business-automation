# app/models/__init__.py

# Import all models
from .user import *  # Your existing user model (keep this)
from .dt_user_story import DtUserStory
from .dt_test_case import DtTestCase
from .dt_task import DtTask
from .dt_generation_log import DtGenerationLog

# Import lookup tables
from .lt_priority import LtPriority
from .lt_general_status import LtGeneralStatus
from .lt_category_ctgry import LtCategoryCtgry
from .lt_role import LtRole

# NEW: CsvUpload
from .dt_csv_upload import CsvUpload

# Make models available for import
__all__ = [
    'User',
    'DtUserStory',
    'DtTestCase',
    'DtTask',
    'DtGenerationLog',
    'LtPriority',
    'LtGeneralStatus',
    'LtCategoryCtgry',
    'LtRole',
    'CsvUpload',        # <-- add this
]
