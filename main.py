from fastapi import FastAPI
from models import DBSession, Item
from sqlalchemy import select
from pydantic import BaseModel

app = FastAPI()


class Items(BaseModel):
    item_name: str
    item_description: str
    item_image_url: str


@app.get("/item/{item_id}")
async def get_item(item_id: int, item_name: str | None = None):
    async with DBSession() as session:
        async with session.begin():
            sql_stmt = select(Item).where(Item.id == item_id)
            print(sql_stmt)
            result = await session.stream_scalars(sql_stmt)
            result: Item = await result.first()
    return {
        "item_name": result.item_name,
        "item_description": result.item_description,
        "item_image_url": result.item_image_url
    }


@app.post("/item/add")
async def add_item(item: Items):
    async with DBSession() as session:
        async with session.begin():
            try:
                item_to_add = Item(**item.dict())
                session.add(item_to_add)
                await session.commit()
                return {
                    "message": "item added",
                    "added_item": item.dict()
                }
            except ValueError as err:
                return {
                    "message": str(err),
                }
