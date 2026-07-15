from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

def get_current_user(
    db: Session = Depends(get_db),
) -> User:
    # Development-only authentication bypass. Restore JWT validation before release.
    user = db.query(User).filter(User.username == "pm").first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Development user not found",
        )
    return user
