from fastapi import FastAPI, Request
from fastapi.security import APIKeyHeader
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .database.db import get_db, Base, engine
from .database.models import APIKey

from .utils.auth import get_api_key, get_current_user

from .routes import classify, auth, tasks, apikeys
from .routes.admin import (tasks as admin_tasks,
                           users as admin_users,
                           apikeys as admin_apikeys)

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

# origins = [
    # "http://localhost",
    # "http://localhost:8080",
# ]

app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(classify.router)
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(apikeys.router)
app.include_router(admin_tasks.router)
app.include_router(admin_users.router)
app.include_router(admin_apikeys.router)

@app.get("/")
async def root(request: Request):
    """
    An HTML welcome page.
    TODO: make dashboard ui for users and admins
    """
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    args = parser.parse_args()
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
