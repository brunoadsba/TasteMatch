"""
Modelos SQLAlchemy (ORM) para o TasteMatch.
Define todas as tabelas do banco de dados.
"""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class User(Base):
    """Modelo de usuário."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    orders = relationship("Order", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)


class Restaurant(Base):
    """Modelo de restaurante."""
    
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    cuisine_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    rating = Column(DECIMAL(2, 1), default=0.0, nullable=False)
    price_range = Column(String(10), nullable=True)  # "low", "medium", "high"
    location = Column(String(255), nullable=True)
    embedding = Column(Text, nullable=True)  # JSON serializado para SQLite, Vector(384) para PostgreSQL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    orders = relationship("Order", back_populates="restaurant")
    recommendations = relationship("Recommendation", back_populates="restaurant")


class Order(Base):
    """Modelo de pedido."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)
    order_date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_amount = Column(DECIMAL(10, 2), nullable=True)
    items = Column(Text, nullable=True)  # JSON array de itens pedidos
    rating = Column(Integer, nullable=True)  # 1 a 5 (opcional)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    user = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")


class Recommendation(Base):
    """Modelo de recomendação."""
    
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)
    similarity_score = Column(DECIMAL(5, 4), nullable=False)  # 0.0 a 1.0
    insight_text = Column(Text, nullable=True)  # Insight gerado pelo LLM
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relacionamentos
    user = relationship("User", back_populates="recommendations")
    restaurant = relationship("Restaurant", back_populates="recommendations")


class UserPreferences(Base):
    """Modelo de preferências agregadas do usuário (cache de embeddings)."""
    
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    preference_embedding = Column(Text, nullable=False)  # JSON array do embedding agregado
    favorite_cuisines = Column(Text, nullable=True)  # JSON array
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    user = relationship("User", back_populates="preferences")

