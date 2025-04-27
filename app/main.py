from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .database.db import Base, engine

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

description = """
A simple REST api to use a MobilenetV2 model trained on Fashion-MNIST data.

Simply Sign up, ask for a new API key and send your image to /classify.
Don't worry about he admin operations. You won't be using them. 
"""

app = FastAPI(
    title="Clothing Image Classifier",
    description=description,
    summary="A simple REST api to use a MobilenetV2 model",
    version="0.0.1",
    contact={
        "name": "Pouya Gharibpour",
        "url": "https://github.com/pouya-gh",
        "email": "p.gharibpour@gmail.com",
    }
)
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
