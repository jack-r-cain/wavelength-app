from sqlmodel import create_engine, SQLModel, Session

# SQLite database URL
# "sqlite:///./wavelength.db" means:
# - sqlite:// = SQLite database
# - ./ = current directory
# - wavelength.db = filename
DATABASE_URL = "sqlite:///./wavelength.db"

# Create engine
# connect_args={"check_same_thread": False} is SQLite-specific
# (allows FastAPI to use it across threads)
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Print all SQL queries (helpful for learning!)
    connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Dependency that provides a database session.
    
    This is used in FastAPI routes:
    @app.get("/items")
    def get_items(session: Session = Depends(get_session)):
        ...
    """
    with Session(engine) as session:
        yield session