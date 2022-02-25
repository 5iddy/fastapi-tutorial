from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from asyncio import current_task
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy import Column, Integer, String, Index
from sqlalchemy import select
from pydantic import BaseModel
from sqlalchemy.orm import validates
from urllib.parse import urlparse
import re


url_validator = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    # domain...
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


Base = declarative_base()


engine: AsyncEngine = create_async_engine(
    "sqlite+aiosqlite:///main.db", echo=False,
)

async_session_factory = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

DBSession = async_scoped_session(
    async_session_factory, scopefunc=current_task
)


class Item(Base):
    __tablename__ = "item"
    id: int = Column(Integer, primary_key=True)
    item_name: str = Column(String(128))
    item_description: str = Column(String(512))
    item_image_url: str = Column(String(2048))

    def __repr__(self):
        return f"Users(id = {self.id}, item_name = '{self.item_name}',\
            item_description = '{self.item_description}', item_image_url='{self.item_image_url}')"

    async def save(self, session: AsyncSession):
        session.add(self)
        await session.commit()

    @validates("item_image_url")
    def validate_image_url(self, key, url):
        if url_validator.fullmatch(url):
            return url
        else:
            raise ValueError(f"invalid url {url}")


async def main():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    info = {
        "item_name": "vivo",
        "item_description": "China piece",
        "item_image_url": "https://localhost/vivo12"
    }

    mobile = Item(item_name="vivo", item_description="China piece",
                  item_image_url="https://localhost/vivo12")
    mobile2 = Item(item_name="iphone", item_description="Apple iphone 6s",
                   item_image_url="https://localhost/iphone6s")
    mobile3 = Item(item_name="redmi", item_description="redmi phone",
                   item_image_url="https://localhost/redmi78")

    async with DBSession() as session:
        async with session.begin():
            session.add(mobile)
            session.add(mobile2)
            session.add(mobile3)
        await session.commit()

        sql_stmt = select(Item)
        print(sql_stmt)
        results = await session.stream_scalars(sql_stmt)

        for row in await results.all():
            print(row)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
