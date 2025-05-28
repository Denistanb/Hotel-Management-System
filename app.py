from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo, MongoClient
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import pickle
import random
from datetime import datetime,timedelta

from bson import ObjectId  # Import ObjectId


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = '5f8c3b1a9d7e4f2c6a0b8e1d3c7f9a4e'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/hotel_management'
mongo = PyMongo(app)









from flask import after_this_request

@app.before_request
def prevent_cache():
    @after_this_request
    def add_no_cache_headers(response):
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.expires = 0
        return response

# # Add this function to prevent caching for admin pages
# @app.after_request
# def add_no_cache_headers(response):
#     # List of admin routes where cache control should be applied
#     admin_routes = ['/admin/dashboard', '/admin/users', '/admin/admin_room_access']
    
#     if request.path in admin_routes:
#         response.cache_control.no_store = True  # Prevent caching
#         response.cache_control.no_cache = True  # Ensure cache is not used
#         response.cache_control.must_revalidate = True  # Force the page to revalidate with the server
    
#     return response



def generate_user_token(name):
    # Hotel name prefix
    hotel_name = "LUX"
    
    # Full username, combine first and last name
    full_username = name.replace(" ", "").upper()  # Removing spaces and converting to uppercase for consistency

    # Get current date in the format YYMMDD
    current_date = datetime.now().strftime('%y%m%d')

    # Generate a random 4-digit number that will ensure uniqueness
    random_number = random.randint(1000, 9999)

    # Combine to create the final user token
    user_token = f"{hotel_name}-{full_username}-{current_date}{random_number}"

    return user_token



@app.route('/')
def home():
    user_token = session.get('user_token')  # Retrieve token from session
    return render_template('index.html', user_token=user_token)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        
        if mongo.db.users.find_one({'email': email}):
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        user_token = generate_user_token(name)  # Generate the unique user token
        
        # Check if the token already exists in the database (to be absolutely sure it's unique)
        while mongo.db.users.find_one({'user_token': user_token}):
            user_token = generate_user_token(name)  # Regenerate token if it already exists
        
        user_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'password': hashed_password,
            'user_token': user_token,
            'created_at': datetime.utcnow()
        }
        
        mongo.db.users.insert_one(user_data)

        # Create secondary user data for frequency booking
        user_data_2 = {
    "user_token": user_token,
    "ssb_count": 0,
    "sdb_count": 0
}

# Insert into freq_booking_collection
        mongo.db.freq_booking_collection.insert_one(user_data_2)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():

    if 'user_token'  in session:
        return redirect(url_for('/'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = mongo.db.users.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])  # Store user_id as a string in session
            session['user_name'] = user['name']
            session['user_token'] = user['user_token']  # Store token in session
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        
        flash('Invalid email or password', 'danger')
    return render_template('login.html')


from datetime import datetime, timedelta

@app.route('/rooms', methods=['GET', 'POST'])
def rooms():
    if 'user_token' not in session:
        flash("Please log in to view your reserved rooms.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session.get('user_id')
        user_name = session.get('user_name')

        # Retrieve user details
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user_data:
            flash('User not found!', 'danger')
            return redirect(url_for('home'))

        user_email = user_data.get('email', '')
        user_phone = user_data.get('phone', '')
        user_token = user_data.get('user_token', '')

        # Retrieve booking details
        room_number = request.form['room_number']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        num_persons = request.form['num_persons']

        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')

        if check_out_date <= check_in_date:
            flash("Check-out date must be later than check-in date.", 'danger')
            return redirect(url_for('rooms'))

        if (check_out_date - check_in_date).days < 1:
            flash("Minimum stay is 1 day.", 'danger')
            return redirect(url_for('rooms'))

        room = mongo.db.rooms.find_one({'room_number': room_number})
        if not room or room['status'] == 'booked':
            flash('Room is not available for booking.', 'danger')
            return redirect(url_for('rooms'))

        # Store booking data
        booking_data = {
            'user_id': user_id,
            'user_name': user_name,
            'user_email': user_email,
            'user_phone': user_phone,
            'user_token': user_token,
            'room_number': room_number,
            'room_type': room['room_type'],
            'num_persons': num_persons,
            'check_in': check_in_date,
            'check_out': check_out_date,
            'booking_date': datetime.utcnow(),
        }

        mongo.db.bookings.insert_one(booking_data)

        mongo.db.rooms.update_one(
            {"room_number": room_number},
            {
                "$set": {
                    "status": "booked",
                    "free_date": check_out_date,
                    "user_token": user_token
                }
            }
        )

        flash('Booking confirmed!', 'success')




        return render_template('booking_confirmation.html', 
                               user_token=user_token, 
                              )

    rooms = mongo.db.rooms.find()
    return render_template('rooms.html', rooms=rooms)



@app.route('/reserved')
def reserved():
    if 'user_token' not in session:
        flash("Please log in to view your reserved rooms.", "danger")
        return redirect(url_for('login'))
    
    user_token = session['user_token']
    
    # Fetch rooms where the user_token matches the logged-in user's token
    reserved_rooms = list(mongo.db.rooms.find({'user_token': user_token}))

    return render_template('reserved.html', rooms=reserved_rooms)



@app.route('/rewards')
def rewards():
    user_token = session.get("user_token")
    
    if not user_token:
        return redirect(url_for("login"))
    
    # Fetch user reward data
    user_data = mongo.db.freq_booking_collection.find_one({"user_token": user_token})

    # Initialize counts
    ssb_count = user_data.get("ssb_count", 0) if user_data else 0
    sdb_count = user_data.get("sdb_count", 0) if user_data else 0


    # Fetch only new bookings
    new_bookings = list(mongo.db.allbookings.find({
        "user_token": user_token,
        "status": "Approved",
    }))

    # Count only the new bookings
    # for booking in new_bookings:
    #     if booking["room_type"] == "Standard Room - Single Bed":
    #         ssb_count += 1
    #     elif booking["room_type"] == "Standard Room - Double Bed":
    #         sdb_count += 1

    # Update freq_booking collection with new counts and last update time
    # mongo.db.freq_booking_collection.update_one(
    #     {"user_token": user_token},
    #     {
    #         "$set": {
    #             "ssb_count": ssb_count,
    #             "sdb_count": sdb_count,
    #         }
    #     },
    #     upsert=True
    # )

    return render_template("rewards_awards.html", new_bookings=new_bookings)






@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if 'user_token' not in session:
        flash('Please login to cancel bookings', 'danger')
        return redirect(url_for('login'))

    room_number = request.form.get('room_number')
    user_token = session['user_token']

    # Update room status in rooms collection
    result = mongo.db.rooms.update_one(
        {'room_number': room_number, 'user_token': user_token},
        {'$set': {
            'status': 'available',
            'user_token': None,
            'free_date': None
        }}
    )

    # Debugging prints
    print("Update Result:", result.modified_count)
    print("Deleting Booking:", mongo.db.bookings.find_one({'room_number': room_number, 'user_token': user_token}))

    # Delete the booking regardless of modified_count
    delete_result = mongo.db.bookings.delete_one({
        'room_number': room_number,
        'user_token': user_token
    })

    if delete_result.deleted_count > 0:
        flash("Booking cancelled successfully!", "success")
    else:
        flash("Error: Booking not deleted!", "danger")

    return redirect(url_for('reserved'))



@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if not session.get('user_id'):
        flash('You must be logged in to book a room!', 'danger')
        return redirect(url_for('login'))
    user_token = session.get('user_token')
    return render_template('booking_confirmation.html', user_token=user_token)



@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_token', None)
    flash('You have logged out successfully!', 'success')
    return redirect(url_for('login'))  # Redirect to login page after logout




def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            print(f"Session does not contain 'admin_id'. Redirecting to login.")
            flash('You need to log in as an admin to access the page.', 'danger')
            return redirect(url_for('admin_login'))  # Redirect to admin login page
        return f(*args, **kwargs)
    return decorated_function



# Admin Login Route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_username = request.form['username']
        admin_password = request.form['password']
        admin = mongo.db.admins.find_one({'username': admin_username})

        if admin and check_password_hash(admin['password'], admin_password):  # Use hashed password check
            session['admin_id'] = str(admin['_id'])
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

# Admin Dashboard Route with login check
@app.route('/admin/dashboard')
@admin_required  # Applying the decorator to require login
def admin_dashboard():
    admin = mongo.db.admins.find_one({'username': "admin"})
        
    if not session['admin_id'] == str(admin['_id']):
        return redirect(url_for('admin_dashboard'))


    bookings = list(mongo.db.bookings.find())
    users = list(mongo.db.users.find())
    return render_template('admin_dashboard.html', bookings=bookings, users=users)

@app.route('/approve_booking/<user_token>/<room_number>', methods=['GET'])
def approve_booking(user_token, room_number):
    """ Approve a booking by updating its status to 'Approved'. """
    booking = mongo.db.bookings.find_one({"user_token": user_token, "room_number": room_number})
    
    if booking:
        mongo.db.bookings.update_one(
            {"user_token": user_token, "room_number": room_number},
            {"$set": {"status": "Approved"}}
        )
    

    
        print("approved Booking:", mongo.db.bookings.find_one({"room_number": room_number, "user_token": user_token}))
    
        new_add = mongo.db.bookings.find_one({"user_token": user_token, "room_number": room_number,"status":"Approved"})
        if new_add:
            mongo.db.allbookings.insert_one(new_add)
        else:
            print("❌ Error: Booking status update might not be reflected immediately.")

        print("approved Booking:", mongo.db.allbookings.find_one({"room_number": room_number, "user_token": user_token}))


        return redirect(url_for('admin_dashboard'))
    
    return "Booking not found", 404


# @app.route('/approve_booking_freq/<user_token>', methods=['GET'])
# def approve_booking_freq(user_token):
#     """ Approve a booking by updating its status to 'Approved'. """
#     booking = mongo.db.freq_booking_collection.find_one({"user_token": user_token})
    
#     if booking:
#         mongo.db.freq_booking_collection.update_one(
#             {"user_token": user_token},
#             {"$set": {"status": "Approved"}}
#         )



#                     # Fetch user reward data
#         user_data = mongo.db.freq_booking_collection.find_one({"user_token": user_token})

#         # Initialize counts
#         ssb_count = user_data.get("ssb_count", 0) if user_data else 0
#         sdb_count = user_data.get("sdb_count", 0) if user_data else 0


#         # Fetch only new bookings
#         new_bookings = list(mongo.db.freq_booking_collection.find({
#             "user_token": user_token,
#             "status": "Approved",
#         }))

#         # Count only the new bookings
#         for booking in new_bookings:
#             if booking["room_type"] == "Standard Room - Single Bed":
#                 ssb_count += 1
#             elif booking["room_type"] == "Standard Room - Double Bed":
#                 sdb_count += 1

#         # Update freq_booking collection with new counts and last update time
#         mongo.db.freq_booking_collection.update_one(
#             {"user_token": user_token},
#             {
#                 "$set": {
#                     "ssb_count": ssb_count,
#                     "sdb_count": sdb_count,
#                 }
#             },
#             upsert=True
#         )







#         return redirect(url_for('admin_dashboard'))
    
#     return "Booking not found", 404

@app.route('/reject_booking/<user_token>/<room_number>', methods=['GET'])
def reject_booking(user_token, room_number):
    """ Reject a booking by deleting it and updating the room status to 'available'. """
    booking = mongo.db.bookings.find_one({"user_token": user_token, "room_number": room_number})
    
    if booking:
        # Update the room's status to available
        result = mongo.db.rooms.update_one(
            {"room_number": room_number, "user_token": user_token},
            {"$set": {
                "status": "available",
                "user_token": None,
                "free_date": None
            }}
        )

        # Debugging output
        print("Update Result:", result.modified_count)
        print("Deleting Booking:", mongo.db.bookings.find_one({"room_number": room_number, "user_token": user_token}))

        # Delete the booking entry from bookings collection
        delete_result = mongo.db.bookings.delete_one({"room_number": room_number, "user_token": user_token})
        delete_result = mongo.db.allbookings.delete_one({"room_number": room_number, "user_token": user_token})

        return redirect(url_for('admin_dashboard'))
    
    return "Booking not found", 404





@app.route('/free_booking/<string:user_token>/<string:room_number>', methods=['GET'])
def free_booking(user_token, room_number):
    """ Free a booking by updating the room status to 'available' and deleting the booking entry. """
    
    # Find the booking based on user_token and room_number
    booking = mongo.db.bookings.find_one({"user_token": user_token, "room_number": room_number})

    if booking:
        # Update the room's status to available and clear user_token and free_date
        result = mongo.db.rooms.update_one(
            {"room_number": room_number, "user_token": user_token},
            {"$set": {
                "status": "available",
                "user_token": None,
                "free_date": None
            }}
        )

        # Debugging output
        print("Update Result:", result.modified_count)

        # Delete the booking entry from bookings collection
        delete_result = mongo.db.bookings.delete_one({"room_number": room_number, "user_token": user_token})
        
        # Debugging output
        print("Deleted Booking:", delete_result.deleted_count)

        return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard

    return "Booking not found", 404  # Handle the case where the booking doesn't exist


@app.route('/admin/users')
@admin_required
def admin_users():
    users = list(mongo.db.users.find())

    for user in users:
        # Initialize ssb_count and sdb_count
        ssb_count = 0
        sdb_count = 0
        
        # Fetch all bookings for the user from the allbookings collection
        bookings = mongo.db.allbookings.find({"user_token": user["user_token"]})

        # Loop through the bookings to increment the counts based on room type
        for booking in bookings:
            if booking["room_type"] == "Standard Room - Single Bed":
                ssb_count += 1
            elif booking["room_type"] == "Standard Room - Double Bed":
                sdb_count += 1

        # Update the freq_booking_collection with the new counts
        mongo.db.freq_booking_collection.update_one(
            {"user_token": user["user_token"]},
            {"$set": {"ssb_count": ssb_count, "sdb_count": sdb_count}},
            upsert=True
        )

        # Add the updated counts to the user dictionary for rendering
        user["ssb_count"] = ssb_count
        user["sdb_count"] = sdb_count

    # Pass the updated user data to the HTML page

    return render_template('admin_users.html', users=users)


@app.route('/delete_user/<user_id>', methods=['GET'])
def delete_user(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if user:
        user_token = user.get("user_token")  # Get user token before deletion
        
        # Delete user from users collection
        mongo.db.users.delete_one({'_id': ObjectId(user_id)})
        
        # Delete all bookings related to the user
        mongo.db.bookings.delete_many({'user_id': str(user_id)})
        

        mongo.db.allbookings.delete_many({'user_id': str(user_id)})


        # Delete user data from freq_booking collection
        mongo.db.freq_booking_collection.delete_one({'user_token': user_token})
        
        # Reset room status for rooms booked by this user
        mongo.db.rooms.update_many(
            {"user_token": user_token},
            {"$set": {"status": "available", "user_token": None, "free_date": None}}
        )

        # Remove session only if the deleted user is currently logged in
        if session.get("user_id") == str(user_id):
            session.pop("user_id", None)
            session.pop("user_token", None)  # Remove only user session
        
        flash('User successfully deleted', 'success')
    else:
        flash('User not found', 'danger')
    
    return redirect(url_for('admin_users'))




# # Delete User
# @app.route('/admin/delete_user/<user_id>')
# @admin_required
# def delete_user(user_id):
#     mongo.db.users.delete_one({'_id': user_id})
#     flash(f"User {user_id} deleted!", 'danger')
#     return redirect(url_for('admin_users'))

# Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin/admin_room_access')
@admin_required
def admin_room_access():
    print("Route is being accessed")
    rooms = list(mongo.db.rooms.find())  
    return render_template('admin_room_acces.html', rooms=rooms)




@app.route('/lock_room/<room_number>', methods=['POST'])
def lock_room(room_number):
    """ Lock a room and set a free date in ISO format """
    free_date = request.form.get('free_date')

    if not free_date:
        return "Free date is required", 400

    # Convert date to full ISO format
    free_date_iso = datetime.strptime(free_date, "%Y-%m-%d")

    room = mongo.db.rooms.find_one({"room_number": room_number})
    if room:
        mongo.db.rooms.update_one(
            {"room_number": room_number},
            {"$set": {"status": "locked", "free_date": free_date_iso}}
        )
        return redirect(url_for('admin_room_access'))
    
    return "Room not found", 404


@app.route('/release_room/<room_number>', methods=['POST'])
def release_room(room_number):
    """ Release a locked room, making it available and clearing free_date """
    room = mongo.db.rooms.find_one({"room_number": room_number})
    if room:
        mongo.db.rooms.update_one(
            {"room_number": room_number},
            {"$set": {"status": "available", "free_date": None}}
        )
        return redirect(url_for('admin_room_access'))
    
    return "Room not found", 404




@app.route("/predict", methods=["GET"])
def predict():
    # Room price mapping
    room_prices = {0: 1000, 1: 1500}  # 0 = Single Bed, 1 = Double Bed
    # Connect to MongoDB (Update URI if required)
    client = MongoClient("mongodb://localhost:27017/")
    db = client["hotel_management"]  # Database name
    collection = db["allbookings"]  # Collection where booking data is stored

    # Load trained Random Forest model
    with open("se_model.pkl", "rb") as f:
        model = pickle.load(f)

    room_prices = {0: 1000, 1: 1500}
    room_types = ["Standard Room - Single Bed" ,"Standard Room - Double Bed"]  # 0 for Single Bed, 1 for Double Bed
    mapping={
        "Standard Room - Single Bed" : 0,
        "Standard Room - Double Bed" : 1
    }
    result = {}

    for room_type in room_types:
        # Step 1: Fetch all documents based on room type
        bookings = list(collection.find({"room_type": room_type}))
        encoded_room_type = mapping[room_type]
        # Step 2: Count number of rooms filled of that type
        num_rooms_filled = len(bookings)

        # If no rooms are filled, set default price and skip calculation
        if num_rooms_filled == 0:
            result[encoded_room_type] = {"final_price" : room_prices[encoded_room_type] }  # Default price for the room type
        else:
            # Step 3: Calculate total number of days stayed
            total_days_stayed = sum((pd.to_datetime(b["check_out"]) - pd.to_datetime(b["check_in"])).days for b in bookings)

            # Step 4: Calculate total price
            total_price = room_prices[encoded_room_type] * total_days_stayed

            # Step 5: Predict profit/loss percentage using trained model
            input_data = np.array([[encoded_room_type, total_days_stayed, num_rooms_filled, total_price]])
            profit_loss_percentage = model.predict(input_data)[0]
            print(total_days_stayed,total_price)
            # Step 6: Calculate adjusted profit/loss
            final_price = ((profit_loss_percentage / 100) * room_prices[encoded_room_type])+room_prices[encoded_room_type]

        # Store the results for this room type
            result[encoded_room_type] = {
            "final_price": round(final_price, 2)
        }

    # You can pass data to the template here
    return render_template('admin_tariff.html', result=result)


if __name__ == '__main__':
    app.run(debug=True)