from pymongo import MongoClient
from datetime import datetime, timedelta

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['hotel_management']

# Create the rooms collection
rooms_collection = db['rooms']

# Room data to be inserted
rooms_data = []

# Adding 10 rooms for Standard Room - Single Bed (Price: 1000)
for i in range(1, 11):
    room = {
        'room_type': 'Standard Room - Single Bed',
        'room_number': f'SSB-{i}',  # Room numbers SSB-1, SSB-2, ..., SSB-10
        'status': 'available',
        'user_token': None,
        'price_per_day': 1000,
        'free_date': None  # Set the free date to the current date (or whenever it's available)
    }
    rooms_data.append(room)

# Adding 10 rooms for Standard Room - Double Bed (Price: 1500)
for i in range(1, 11):
    room = {
        'room_type': 'Standard Room - Double Bed',
        'room_number': f'SDB-{i}',  # Room numbers SDB-1, SDB-2, ..., SDB-10
        'status': 'available',
        'user_token': None,
        'price_per_day': 1500,
        'free_date': None  # Set the free date to the current date
    }
    rooms_data.append(room)

# Insert the rooms data into the collection
rooms_collection.insert_many(rooms_data)

print("10 Single Bed rooms and 10 Double Bed rooms added to the database successfully!")
