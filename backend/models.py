from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)

    # cascade="all, delete-orphan" ensures if a user account is deleted, their shoes are deleted too
    inventory = relationship("InventoryItem", back_populates="owner", cascade="all, delete-orphan")

class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    upc = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    size = Column(String)
    condition = Column(String)
    purchase_price = Column(Float, nullable=False, default=0.0)
    status = Column(String, default="In Stock", nullable=False)
    
    # ForeignKey strictly links this row to a specific ID in the users table
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # back_populates establishes the two-way virtual link back to the User model
    owner = relationship("User", back_populates="inventory")