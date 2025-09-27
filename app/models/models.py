from sqlalchemy import BigInteger, String, ForeignKey, TIMESTAMP, func, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())

class Product(Base):
    __tablename__ = 'products'
    product_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Используем Numeric для рублей и копеек
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

class Order(Base):
    __tablename__ = 'orders'
    order_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    # Убедитесь, что здесь тоже правильный ForeignKey
    product_id: Mapped[int] = mapped_column(ForeignKey('products.product_id'))
    status: Mapped[str] = mapped_column(String(50), default='new')
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())