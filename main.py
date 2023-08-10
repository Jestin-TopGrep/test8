from fastapi import FastAPI, HTTPException, Header, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from fastapi.middleware.cors import CORSMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
import random
import string


app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class Tasks(BaseModel):
    id: int
    title: str
    description: str

expected_credentials = {
    "username": "querty",
    "password": "querty123"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

exp_token = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

tasks = [
    Tasks(id=1, title="Finish repor", description="Complete project report by friday"),
    Tasks(id=2, title="Finish the book", description="Finish reading the new novel and start another one"),
    Tasks(id=3, title="Exercise", description="Go to the gym for cardio"),
]

@app.get('/')
def home():
    return {"message": "This is your Task Management API. Proceed to '/tasks' to view the tasks"}


@app.post('/authenticate')
@limiter.limit("2/minute")
def authenticate_user(credentials: dict, request: Request):
    provided_username = credentials.get('username')
    provided_password = credentials.get('password')
    if provided_username == expected_credentials['username'] and provided_password == expected_credentials['password']: 
        return {"message": "Authentication successful", "token": exp_token}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# get all tasks
@app.get('/tasks')
@limiter.limit("5/minute")
def get_tasks(request: Request):
    return tasks

# get tasks by id
@app.get('/tasks/{task_id}')
@limiter.limit("3/minute")
def get_by_id(task_id: int, request: Request):
    if task_id <= len(tasks):
        for task in tasks:
            if task.id == task_id:
                return task
    raise HTTPException(status_code=404, detail="Task not found")

# post tasks
@app.post('/tasks')
@limiter.limit("5/minute")
def add_tasks(task: Tasks, request: Request):
    if any(taskItem.id == task.id for taskItem in tasks):
        raise HTTPException(status_code=400, detail="Task with the same id already exists")
    tasks.append(task)
    return {"message": f"Task '{task.title}' added successfully", "task": task}

# update tasks
@app.put('/tasks/{task_id}')
@limiter.limit("4/minute")
def update_by_id(task_id: int, updated_task: Tasks, request: Request):
    if task_id > 0 and task_id <= len(tasks):
        for task in tasks:
            if task.id == task_id:
                task.title = updated_task.title
                task.description = updated_task.description
        return {"message": f"Task updated successfully", "task": updated_task}
    raise HTTPException(status_code=404, detail="No task with the provided id")

# Delete by id
@app.delete('/tasks/{task_id}')
@limiter.limit("3/minute")
def delete_by_id(task_id: int, request: Request, authorization: str = Header()):
    if authorization == exp_token:
        if task_id > 0 and task_id <= len(tasks):
            for task in tasks:
                if task.id == task_id:
                    tasks.remove(task)
                    return {"message": f"Authorization succesful and task deleted successfully"}
                else:
                    return {"message": f"Task not found with the provided Id"}
    raise HTTPException(status_code=404, detail="Authorization not succesful")

