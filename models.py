from flask_login import UserMixin

from db import users_collection, items_collection, reviews_collection
from abc import ABC, abstractmethod
from datetime import datetime
from bson.objectid import ObjectId


class User(UserMixin):
    def __init__(self, username='John Doe', pwd='', is_admin=False, id=None):
        self.username = username
        self.pwd = pwd
        self.id = id
        self.is_admin = is_admin

    def __str__(self):
        return self.username

    def save(self):
        result = users_collection.insert_one(
            {"username": self.username, "pwd": self.pwd,
             'is_admin': self.is_admin})
        self.id = result.inserted_id

    @staticmethod
    def get_by_username(username):
        user = users_collection.find_one({"username": username})
        if user:
            return User(username=user["username"], pwd=user['pwd'],
                        is_admin=user['is_admin'], id=user['_id'])
        else:
            return None

    @staticmethod
    def get_by_id(user_id):
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return User(username=user["username"], pwd=user['pwd'],
                        id=user['_id'], is_admin=user['is_admin'])
        else:
            return None

    def get_reviews(self):
        return Review.get_by_user(self.id)

    def get_avg_rating(self):
        reviews = self.get_reviews()
        if not reviews:
            return 0
        rating = 0
        for review in reviews:
            rating += review.rating
        return rating / len(reviews)


class Item(ABC):
    @abstractmethod
    def __init__(self, name, description, price, seller, image, _id=None, **kwargs):
        self.name = name
        self.description = description
        self.price = price
        self.seller = seller
        self.image = image
        self.created_at = datetime.utcnow()
        self._id = _id

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'seller': self.seller,
            'image': self.image,
            'created_at': self.created_at
        }

    def save(self):
        result = items_collection.insert_one(self.to_dict())
        self._id = result.inserted_id

    def get_seller(self):
        return User.get_by_id(ObjectId(self.seller))

    def get_reviews(self):
        return Review.get_by_item(self._id)

    def get_review_count(self):
        return len(self.get_reviews())

    def get_rating(self):
        reviews = self.get_reviews()
        if not reviews:
            return 0
        rating = 0
        for review in reviews:
            rating += review.rating
        return rating / len(reviews)

    @staticmethod
    def get_by_id(item_id):
        item_dict = items_collection.find_one({'_id': ObjectId(item_id)})
        if item_dict is None:
            return None
        item_type = item_dict.pop('item_type')
        if item_type == 'Clothing':
            item = Clothing(**item_dict)
        elif item_type == 'ComputerComponent':
            item = ComputerComponent(**item_dict)
        elif item_type == 'Monitor':
            item = Monitor(**item_dict)
        elif item_type == 'Snack':
            item = Snack(**item_dict)
        else:
            raise ValueError(f'Unknown item type: {item_type}')
        item._id = str(item_dict['_id'])
        return item


class Clothing(Item):
    def __init__(self, name, description, price, seller, image, color, size, **kwargs):
        super().__init__(name, description, price, seller, image, **kwargs)
        self.color = color
        self.size = size
        self.item_type = 'Clothing'

    def to_dict(self):
        item_dict = super().to_dict()
        item_dict['color'] = self.color
        item_dict['size'] = self.size
        item_dict['item_type'] = self.item_type
        return item_dict


class ComputerComponent(Item):
    def __init__(self, name, description, price, seller, image, spec, **kwargs):
        super().__init__(name, description, price, seller, image, **kwargs)
        self.spec = spec
        self.item_type = 'ComputerComponent'

    def to_dict(self):
        item_dict = super().to_dict()
        item_dict['spec'] = self.spec
        item_dict['item_type'] = self.item_type
        return item_dict


class Monitor(Item):
    def __init__(self, name, description, price, seller, image, spec, **kwargs):
        super().__init__(name, description, price, seller, image, **kwargs)
        self.spec = spec
        self.item_type = 'Monitor'

    def to_dict(self):
        item_dict = super().to_dict()
        item_dict['spec'] = self.spec
        item_dict['item_type'] = self.item_type
        return item_dict


class Snack(Item):
    def __init__(self, name, description, price, seller, image, **kwargs):
        super().__init__(name, description, price, seller, image, **kwargs)
        self.item_type = 'Snack'

    def to_dict(self):
        item_dict = super().to_dict()
        item_dict['item_type'] = self.item_type
        return item_dict


ITEM_TYPES = {
    'Clothing': Clothing,
    'ComputerComponent': ComputerComponent,
    'Monitor': Monitor,
    'Snack': Snack,
}


class Review:
    def __init__(self, item, creator, rating, text='', created_at=datetime.utcnow(), _id=None):
        self.text = text
        self.item = item
        self.creator = creator
        self.rating = rating
        self._id = _id
        self.created_at = created_at

    def to_dict(self):
        return {
            'text': self.text,
            'item': self.item,
            'creator': self.creator,
            'rating': self.rating,
            'created_at': self.created_at
        }

    def save(self):
        result = reviews_collection.insert_one(self.to_dict())
        self._id = result.inserted_id

    def update(self, update_dict):
        reviews_collection.find_one_and_update(filter={'_id': ObjectId(self._id)}, update={'$set': update_dict})

    def get_creator(self):
        return User.get_by_id(self.creator)

    def get_item(self):
        return Item.get_by_id(self.item)

    @staticmethod
    def get_by_id(id):
        review = reviews_collection.find_one({"_id": ObjectId(id)})
        if review:
            return Review(**review)
        else:
            return None

    @staticmethod
    def get_by_item(item_id):
        return [Review(**dic) for dic in reviews_collection.find({'item': ObjectId(item_id)})]

    @staticmethod
    def get_by_user(user_id):
        return [Review(**dic) for dic in reviews_collection.find({'creator': ObjectId(user_id)})]
