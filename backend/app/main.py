from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import items
from .database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    Code before yield runs on startup.
    Code after yield runs on shutdown.
    """
    # Startup: Create database tables
    create_db_and_tables()
    print("✅ Database tables created")
    
    yield  # Application is running
    
    # Shutdown: Cleanup code 
    print("👋 Shutting down")

app = FastAPI(title="Wavelength API", description="Personal influence archive with AI-powered connections",
    version="0.1.0",
    lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(items.router)

@app.get("/")
def read_root():
    return {"message": "Wavelength API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
