from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from bson import ObjectId
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db
from app.models.user import UserCreate, LoginRequest, Token, UserResponse

router = APIRouter(prefix="/auth", tags=["احراز هویت"])
security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM
    )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=401, detail="توکن نامعتبر است")
    except JWTError:
        raise HTTPException(status_code=401, detail="توکن نامعتبر یا منقضی شده است")

    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="کاربر یافت نشد")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="حساب کاربری غیرفعال است")

    user["id"] = str(user.pop("_id"))
    return user


async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="فقط مدیران به این بخش دسترسی دارند")
    return current_user


async def require_farmer(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ("farmer", "admin"):
        raise HTTPException(status_code=403, detail="فقط کشاورزان به این بخش دسترسی دارند")
    return current_user


@router.post("/register", response_model=UserResponse, summary="ثبت‌نام کاربر جدید")
async def register(user_data: UserCreate):
    db = get_db()
    existing = await db.users.find_one({"username": user_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="نام کاربری قبلاً استفاده شده است")

    user = {
        "username": user_data.username,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role.value,
        "full_name": user_data.full_name,
        "phone": user_data.phone,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user)
    user["id"] = str(result.inserted_id)
    del user["_id"]
    del user["password_hash"]
    return user


@router.post("/login", response_model=Token, summary="ورود به سیستم")
async def login(credentials: LoginRequest):
    db = get_db()
    user = await db.users.find_one({"username": credentials.username})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور اشتباه است")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="حساب کاربری غیرفعال است")

    token = create_token(str(user["_id"]), user["role"])
    return Token(
        access_token=token,
        role=user["role"],
        user_id=str(user["_id"]),
        full_name=user["full_name"],
    )


@router.get("/me", response_model=UserResponse, summary="دریافت اطلاعات کاربر جاری")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
