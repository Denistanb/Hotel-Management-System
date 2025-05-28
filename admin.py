from pymongo import MongoClient
from werkzeug.security import generate_password_hash

client = MongoClient("mongodb://localhost:27017/")
db = client.hotel_management

# Create an admin user with a hashed password
admin_data = {
    "username": "admin",
    "password": generate_password_hash("admin123"),  # Change password here
}

# Insert into the "admins" collection
db.admins.insert_one(admin_data)

print("Admin user created successfully!")
