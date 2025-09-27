from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import User, Product, Order

class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(self, user_id: int, username: str, first_name: str):
        user_exists = await self.session.get(User, user_id)
        if not user_exists:
            new_user = User(user_id=user_id, username=username, first_name=first_name)
            self.session.add(new_user)
            await self.session.commit()

    async def get_all_products(self):
        query = select(Product)
        result = await self.session.execute(query)
        return result.scalars().all()

    # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
    async def add_product(self, name: str, price: float):
        new_product = Product(name=name, price=price)
        self.session.add(new_product)
        await self.session.commit()
        return new_product

    async def delete_product(self, product_id: int):
        product = await self.session.get(Product, product_id)
        if product:
            await self.session.delete(product)
            await self.session.commit()
            return True
        return False
        
    async def create_order(self, user_id: int, product_id: int) -> Order:
        new_order = Order(user_id=user_id, product_id=product_id)
        self.session.add(new_order)
        await self.session.flush()
        await self.session.refresh(new_order)
        await self.session.commit()
        return new_order