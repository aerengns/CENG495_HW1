from flask_pymongo import pymongo
from pymongo.collection import Collection
from dotenv import load_dotenv
import os

load_dotenv()
connection_string = os.getenv('CONNECTION_STRING')
client = pymongo.MongoClient(connection_string)
db = client.get_database('myDB')

users_collection = db['users']
items_collection = db['items']
reviews_collection = db['reviews']