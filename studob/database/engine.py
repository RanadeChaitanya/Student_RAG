from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class DatabaseEngine:
    def __init__(self, url: str, echo: bool = False, pool_size: int = 5, max_overflow: int = 10):
        if "sqlite" in url:
            self._engine = create_async_engine(url, echo=echo)
        else:
            self._engine = create_async_engine(
                url, echo=echo, pool_size=pool_size, max_overflow=max_overflow
            )
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close_db(self) -> None:
        await self._engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    def get_session_factory(self):
        return self._session_factory
