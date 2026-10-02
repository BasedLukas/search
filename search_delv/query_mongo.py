from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017'), connect=False)
db = client[os.getenv('MONGODB_DB', 'scraping_db')]
collection = db[os.getenv('MONGODB_COLLECTION', 'webpages')]

# Function to get a field by _id or url
def get_field_by_id_or_url(identifier, field_name):
    if ObjectId.is_valid(identifier):
        query = {'_id': ObjectId(identifier)}
    else:
        query = {'url': identifier}
    document = collection.find_one(query, {field_name: 1, '_id': 0})
    return document.get(field_name) if document else None

# Function to get all values of a field
def get_all_values_of_field(field_name):
    cursor = collection.find({}, {field_name: 1, '_id': 0})
    values = [doc.get(field_name) for doc in cursor]
    return values

# Filtered query functions
def get_documents_by_status_code(status_code):
    cursor = collection.find({'status_code': status_code})
    return list(cursor)

def get_documents_by_content_length_gt(value):
    cursor = collection.find({'content_length': {'$gt': value}})
    return list(cursor)

def get_documents_crawled_after(date_string):
    date = datetime.fromisoformat(date_string)
    cursor = collection.find({'crawled_at': {'$gt': date}})
    return list(cursor)

def get_documents_by_meta_language(language):
    cursor = collection.find({'meta_language': language})
    return list(cursor)

def get_documents_with_title_containing(keyword):
    cursor = collection.find({'title': {'$regex': keyword, '$options': 'i'}})
    return list(cursor)

def get_all_unique_urls():
    urls = collection.distinct('url')
    return urls

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Inspect a field in a MongoDB collection')
    parser.add_argument('identifier', help='MongoDB ObjectId or source URL')
    parser.add_argument('field', nargs='?', default='title')
    args = parser.parse_args()
    print(get_field_by_id_or_url(args.identifier, args.field))
