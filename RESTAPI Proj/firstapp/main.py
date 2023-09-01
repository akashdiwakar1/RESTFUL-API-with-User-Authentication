from datetime import datetime, timedelta
from typing import Union
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from typing_extensions import Annotated

DATABASE_URL = "postgresql://postgres:postgres@localhost/firstappDB"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Taskit(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    description = Column(String)
    project_id = Column(Integer)
    completed = Column(Boolean)

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None

class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None

class UserInDB(User):
    hashed_password: str

class Task(BaseModel):
    description: str
    project_id: int
    completed: bool

class TaskUpdate(BaseModel):
    description: str
    project_id: int
    completed: bool

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

@app.post("/tasks/")
async def create_task(task: Task, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_task = Taskit(
        username=current_user.username,
        description=task.description,
        project_id=task.project_id,
        completed=task.completed
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {"message": "Task created successfully", "task": db_task}

@app.get("/tasks/")
async def get_user_tasks(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user_tasks = db.query(Taskit).filter(Taskit.username == current_user.username).all()
    return user_tasks

@app.get("/tasks/{task_id}")
async def get_task_by_id(task_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    task = db.query(Taskit).filter(Taskit.id == task_id, Taskit.username == current_user.username).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: TaskUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_task = db.query(Taskit).filter(Taskit.id == task_id, Taskit.username == current_user.username).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in task.dict().items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_task = db.query(Taskit).filter(Taskit.id == task_id, Taskit.username == current_user.username).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}
