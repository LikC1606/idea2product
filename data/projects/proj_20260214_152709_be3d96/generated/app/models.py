from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class ProductRequest(Base):
    __tablename__ = 'product_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_filename = Column(String(255), nullable=False)  # Stores the uploaded image filename
    needs_description = Column(Text, nullable=False)  # Stores the user-provided description
    generated_title = Column(String(255), nullable=True)  # Stores the generated product title
    selling_point_1 = Column(String(255), nullable=True)  # Stores the first selling point
    selling_point_2 = Column(String(255), nullable=True)  # Stores the second selling point
    selling_point_3 = Column(String(255), nullable=True)  # Stores the third selling point
    created_at = Column(DateTime, default=datetime.utcnow)  # Timestamp for request creation

    def __repr__(self):
        return f"<ProductRequest(id={self.id}, image_filename='{self.image_filename}', created_at='{self.created_at}')>"