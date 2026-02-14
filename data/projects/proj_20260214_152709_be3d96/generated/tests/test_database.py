import unittest
from app.database import get_db, Base
from app.models import ProductContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestDatabaseModelsAndQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup in-memory SQLite database for testing
        cls.engine = create_engine('sqlite:///:memory:')
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        cls.session = SessionLocal()
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        # Drop all tables and close the database connection
        Base.metadata.drop_all(bind=cls.engine)
        cls.session.close()

    def setUp(self):
        # Clear the database before each test
        self.session.query(ProductContent).delete()
        self.session.commit()

    def test_product_content_model(self):
        # Test creation of a ProductContent model instance
        product = ProductContent(
            image_url="http://example.com/image.jpg",
            needs_description="A sleek, modern chair for office use.",
            product_title="Ergonomic Office Chair",
            selling_points=["Comfortable for long hours", "Modern design", "Adjustable height"]
        )
        self.session.add(product)
        self.session.commit()

        # Retrieve and assert the product data
        retrieved_product = self.session.query(ProductContent).first()
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.image_url, "http://example.com/image.jpg")
        self.assertEqual(retrieved_product.needs_description, "A sleek, modern chair for office use.")
        self.assertEqual(retrieved_product.product_title, "Ergonomic Office Chair")
        self.assertEqual(retrieved_product.selling_points, ["Comfortable for long hours", "Modern design", "Adjustable height"])

    def test_query_product_content(self):
        # Test querying product content from the database
        product1 = ProductContent(
            image_url="http://example.com/image1.jpg",
            needs_description="A durable outdoor table.",
            product_title="Outdoor Patio Table",
            selling_points=["Weather-resistant", "Stylish design", "Easy to assemble"]
        )
        product2 = ProductContent(
            image_url="http://example.com/image2.jpg",
            needs_description="A compact and efficient blender.",
            product_title="Portable Blender",
            selling_points=["Compact size", "Powerful motor", "Easy to clean"]
        )
        self.session.add_all([product1, product2])
        self.session.commit()

        results = self.session.query(ProductContent).all()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].product_title, "Outdoor Patio Table")
        self.assertEqual(results[1].product_title, "Portable Blender")

    def test_update_product_content(self):
        # Test updating an existing product content
        product = ProductContent(
            image_url="http://example.com/image.jpg",
            needs_description="A sturdy bookshelf.",
            product_title="Wooden Bookshelf",
            selling_points=["Elegant design", "Spacious shelves", "Durable material"]
        )
        self.session.add(product)
        self.session.commit()

        # Update the product title and selling points
        product_to_update = self.session.query(ProductContent).first()
        product_to_update.product_title = "Modern Wooden Bookshelf"
        product_to_update.selling_points = ["Contemporary design", "Compact size", "Eco-friendly material"]
        self.session.commit()

        # Retrieve and assert the updated product data
        updated_product = self.session.query(ProductContent).first()
        self.assertEqual(updated_product.product_title, "Modern Wooden Bookshelf")
        self.assertEqual(updated_product.selling_points, ["Contemporary design", "Compact size", "Eco-friendly material"])

    def test_delete_product_content(self):
        # Test deleting a product content entry
        product = ProductContent(
            image_url="http://example.com/image.jpg",
            needs_description="A versatile kitchen knife.",
            product_title="Chef's Knife",
            selling_points=["Sharp blade", "Ergonomic handle", "Rust-resistant"]
        )
        self.session.add(product)
        self.session.commit()

        # Delete the product
        product_to_delete = self.session.query(ProductContent).first()
        self.session.delete(product_to_delete)
        self.session.commit()

        # Assert the product no longer exists
        deleted_product = self.session.query(ProductContent).first()
        self.assertIsNone(deleted_product)

if __name__ == '__main__':
    unittest.main()