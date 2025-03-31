from fastapi import APIRouter, HTTPException
from typing import List
from server.schemas.user import User, UserCreate
from server.utils.helpers import get_users

router = APIRouter()
