######################################################################
# Product API Service Test Suite
######################################################################
import os
import logging
from decimal import Decimal
from unittest import TestCase
from urllib.parse import quote_plus

from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        db.session.close()

    def setUp(self):
        self.client = app.test_client()
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ##################################################################
    # Utility
    ##################################################################
    def _create_products(self, count=1):
        products = []
        for _ in range(count):
            product = ProductFactory()
            response = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            new_product = response.get_json()
            product.id = new_product["id"]
            products.append(product)
        return products

    ##################################################################
    # TESTS
    ##################################################################

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_product(self):
        product = ProductFactory()
        response = self.client.post(BASE_URL, json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.get_json()
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(Decimal(data["price"]), product.price)
        self.assertEqual(data["available"], product.available)
        self.assertEqual(data["category"], product.category.name)

    def test_get_product(self):
        product = self._create_products(1)[0]
        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], product.name)

    def test_get_product_not_found(self):
        response = self.client.get(f"{BASE_URL}/9999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        product = self._create_products(1)[0]
        product.description = "Updated Description"

        response = self.client.put(
            f"{BASE_URL}/{product.id}",
            json=product.serialize()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(data["description"], "Updated Description")

    def test_delete_product(self):
        product = self._create_products(1)[0]

        response = self.client.delete(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_products(self):
        self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_query_by_name(self):
        products = self._create_products(5)
        name = products[0].name

        response = self.client.get(
            BASE_URL,
            query_string=f"name={quote_plus(name)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_query_by_category(self):
        products = self._create_products(5)
        category = products[0].category

        response = self.client.get(
            BASE_URL,
            query_string=f"category={category.name}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_query_by_availability(self):
        self._create_products(5)

        response = self.client.get(
            BASE_URL,
            query_string="available=true"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
