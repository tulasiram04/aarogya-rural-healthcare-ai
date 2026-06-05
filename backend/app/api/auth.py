from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.exceptions import CredentialsException
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login-form")

def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """Dependency to retrieve the currently authenticated user from their JWT token."""
    payload = decode_access_token(token)
    if not payload:
        raise CredentialsException()
    
    user_id = payload.get("sub")
    if not user_id:
        raise CredentialsException()
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise CredentialsException("User account is disabled or missing")
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create a new doctor or healthcare worker profile."""
    # Check if user already exists
    existing = db.query(User).filter(User.phone == user_in.phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this phone number already exists."
        )
        
    hashed_pwd = get_password_hash(user_in.password)
    db_user = User(
        phone=user_in.phone,
        full_name=user_in.full_name,
        email=user_in.email,
        role=user_in.role,
        hashed_password=hashed_pwd,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    """Authenticate credentials and return JWT bearer token."""
    user = db.query(User).filter(User.phone == login_in.phone).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect phone number or password"
        )
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-form", response_model=Token)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Standard OAuth2 form-compatible login endpoint for automated API utilities (Swagger)."""
    user = db.query(User).filter(User.phone == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect phone number or password"
        )
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Retrieve profile details of the logged-in doctor/HCW."""
    return current_user
