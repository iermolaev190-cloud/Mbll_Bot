from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/db_name"

# Create an async SQLAlchemy engine
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Create a session maker for asynchronous sessions
async_session_maker = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session():
    async with async_session_maker() as session:
        yield session

async def init_db():
    async with async_engine.begin() as conn:
        # Include your database initialization logic here
        pass  

async def close_db():
    await async_engine.dispose()