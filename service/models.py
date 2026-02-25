import logging
from enum import Enum
from decimal import Decimal
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

db = SQLAlchemy()


def init_db(app: Flask):
    """Initialize the database"""
    Product.init_db(app)


class DataValidationError(Exception):
    """Used for data validation errors when deserializing"""


class Category(Enum):
    """Enumeration of valid Product Categories"""
    UNKNOWN = 0
    CLOTHS = 1
    FOOD = 2
    HOUSEWARES = 3
    AUTOMOTIVE = 4
    TOOLS = 5


class Product(db.Model):
    """Product model using SQLAlchemy"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    available = db.Column(db.Boolean, nullable=False, default=True)
    category = db.Column(
        db.Enum(Category), nullable=False, server_default=(Category.UNKNOWN.name)
    )

    def __repr__(self):
        return f"<Product {self.name} id=[{self.id}]>"

    def create(self):
        """Creates a Product in the database"""
        logger.info("Creating %s", self.name)
        self.id = None
        db.session.add(self)
        db.session.commit()

    def update(self):
        """Updates a Product in the database"""
        logger.info("Saving %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        db.session.commit()

    def delete(self):
        """Removes a Product from the data store"""
        logger.info("Deleting %s", self.name)
        db.session.delete(self)
        db.session.commit()

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": str(self.price),
            "available": self.available,
            "category": self.category.name
        }

    def deserialize(self, data: dict):
        try:
            self.name = data["name"]
            self.description = data["description"]
            self.price = Decimal(data["price"])
            self.available = bool(data["available"])
            self.category = getattr(Category, data["category"])
        except KeyError as error:
            raise DataValidationError("Missing field: " + error.args[0])
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0])
        except TypeError as error:
            raise DataValidationError("Invalid data: " + str(error))
        return self

    @classmethod
    def init_db(cls, app: Flask):
        """Initializes the database"""
        logger.info("Initializing database")
        db.init_app(app)
        app.app_context().push()
        db.create_all()

    @classmethod
    def all(cls) -> list:
        return cls.query.all()

    @classmethod
    def find(cls, product_id: int):
        return cls.query.get(product_id)

    @classmethod
    def find_by_name(cls, name: str) -> list:
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_price(cls, price: Decimal) -> list:
        if isinstance(price, str):
            price = Decimal(price.strip(' "'))
        return cls.query.filter(cls.price == price)

    @classmethod
    def find_by_availability(cls, available: bool = True) -> list:
        return cls.query.filter(cls.available == available)

    @classmethod
    def find_by_category(cls, category: Category = Category.UNKNOWN) -> list:
        return cls.query.filter(cls.category == category)
