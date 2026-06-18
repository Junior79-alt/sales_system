from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from database import engine, Base
from routes import users, sales

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sales Management System",
    description="API with user activation",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(users.router)
app.include_router(sales.router)

# Dashboard
dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")

@app.get("/")
def root():
    return {"message": "Sales System with User Activation", "dashboard": "/dashboard/login.html"}

@app.get("/health")
def health():
    return {"status": "OK"}