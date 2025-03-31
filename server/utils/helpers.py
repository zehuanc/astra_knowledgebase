from typing import List
from server.schemas.user import User

def format_date(date):
    """Format date"""
    return date.strftime('%Y-%m-%d %H:%M:%S')

def get_users() -> List[User]:
    """Get list of users (mock function)"""
    return [
        User(id=1, username="john", email="john@example.com"),
        User(id=2, username="jane", email="jane@example.com")
    ] 