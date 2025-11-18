from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from ..auth import VALID_ROLES, create_user, delete_user, get_current_user, list_users


router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Literal["admin", "general"]


def _ensure_admin(user) -> None:
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges are required for this action",
        )


@router.get("")
def get_users(user=Depends(get_current_user)):
    _ensure_admin(user)
    return list_users()


@router.post("", status_code=201)
def add_user(payload: UserCreate, user=Depends(get_current_user)):
    _ensure_admin(user)
    return create_user(payload.email, payload.password, payload.role)


@router.delete("/{email}")
def remove_user(email: str, user=Depends(get_current_user)):
    _ensure_admin(user)
    delete_user(email)
    return {"status": "deleted"}
