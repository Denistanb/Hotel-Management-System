# 🏨 Hotel Management System

Welcome to the **Hotel Management System** – a full-featured hotel management web application designed to streamline and automate hotel operations, improve customer experience, and support hotel staff with intuitive tools and analytics.

This project is ideal for educational purposes, beginner Flask developers, or anyone looking to understand how web-based administrative systems can be built with Python.

---

## 🚀 Features

- 🛏️ **Room Management**: Add, edit, and track room availability, features, and pricing.
- 👤 **Customer Management**: Record and manage customer details, bookings, check-ins, and check-outs.
- 📊 **Dashboard with Analytics**: Real-time visualization of key metrics using charts and graphs.
- 🤖 **ML-Powered Prediction**: Integrates a trained machine learning model to predict customer satisfaction based on inputs.
- 🔐 **Admin Interface**: Separate admin functionality for secure management of backend operations.
- 🧹 **Clean UI**: HTML and CSS templates with user-friendly navigation and layout.

---

## 🛠️ Tech Stack

| Layer             | Technology               |
|-------------------|--------------------------|
| **Frontend**      | HTML5, CSS3, JavaScript  |
| **Backend**       | Python, Flask            |
| **Database**      | SQLite                   |
| **ML Model**      | Scikit-learn, Pandas     |
| **Visualization** | Matplotlib, Plotly       |

---

## 📈 Machine Learning Integration

The system uses a **supervised machine learning model** trained on the `hotel_dataset.csv`. This model helps predict:

- Likelihood of customer satisfaction
- Features contributing to dissatisfaction
- Insights into customer preferences

The model (`se_model.pkl`) is serialized using `joblib` and loaded in real-time within the Flask application.

---

## ⚙️ Installation

Follow these steps to run the project locally:

# Clone the repository
```bash
git clone https://github.com/Denistanb/Hotel-Management-System.git
cd Hotel-Management-System
```

# Install dependencies
```bash
pip install -r requirements.txt
```

# Run the Flask app
```bash
python app.py
```
