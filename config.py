import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Persistent Storage Path
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "reading_list.json"

# Supported Statuses
STATUS_UNREAD = "unread"
STATUS_READING = "reading"
STATUS_COMPLETED = "completed"
VALID_STATUSES = {STATUS_UNREAD, STATUS_READING, STATUS_COMPLETED}

# Standard Categories
STANDARD_CATEGORIES = [
    "technology",
    "AI/ML",
    "programming",
    "business",
    "finance",
    "productivity",
    "self-help",
    "fiction",
    "biography",
    "science",
    "general"
]

# Normalization Map for common user variations
CATEGORY_NORMALIZATION_MAP = {
    "ai": "AI/ML",
    "ml": "AI/ML",
    "ai/ml": "AI/ML",
    "artificial intelligence": "AI/ML",
    "machine learning": "AI/ML",
    "tech": "technology",
    "technology": "technology",
    "code": "programming",
    "coding": "programming",
    "programming": "programming",
    "software": "programming",
    "self help": "self-help",
    "self-help": "self-help",
    "personal development": "self-help",
    "money": "finance",
    "finance": "finance",
    "investing": "finance",
    "productivity": "productivity",
    "time management": "productivity",
    "biz": "business",
    "business": "business",
    "bio": "biography",
    "biography": "biography",
    "sci-fi": "fiction",
    "fiction": "fiction",
    "science": "science",
    "general": "general"
}
