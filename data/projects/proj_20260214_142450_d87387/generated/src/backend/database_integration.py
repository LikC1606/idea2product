import os
from src.database.database_setup import DatabaseConnection
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

class DatabaseIntegration:
    def __init__(self, db_uri=None):
        self.db_uri = db_uri or os.getenv('DATABASE_URI')
        self.db_connection = DatabaseConnection(self.db_uri)
        self.Session = sessionmaker(bind=self.db_connection.engine)

    def store_product_description(self, user_id, image_path, description, generated_title, selling_points):
        session = self.Session()
        try:
            product_data = {
                'user_id': user_id,
                'image_path': image_path,
                'description': description,
                'generated_title': generated_title,
                'selling_points': selling_points
            }
            session.add(ProductDescription(**product_data))
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error storing product description: {str(e)}")
            raise
        finally:
            session.close()

    def retrieve_product_description(self, product_id):
        session = self.Session()
        try:
            product_description = session.query(ProductDescription).filter_by(id=product_id).one_or_none()
            return product_description
        except SQLAlchemyError as e:
            print(f"Error retrieving product description: {str(e)}")
            raise
        finally:
            session.close()

# Define ProductDescription model
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ProductDescription(Base):
    __tablename__ = 'product_descriptions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    image_path = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    generated_title = Column(String(255), nullable=False)
    selling_points = Column(Text, nullable=False)

# Ensure the database tables are created
Base.metadata.create_all(DatabaseConnection().engine)