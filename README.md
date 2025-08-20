# 🍽️ Food Wastage Management System

This project is a **Streamlit web application** that helps track and manage **food listings, claims, providers, and receivers** to reduce food wastage.  
It uses **SQLite** for storing data and provides **visual insights** into food demand vs supply.

---

## 🚀 Features
- Upload and manage **food listings** from providers
- Track **claims** from receivers
- Analyze **demand vs supply**
- Interactive **charts and reports**
- Simple, lightweight, and runs in the browser

---

## 📂 Project Structure
.
├── data/
│ ├── claims_data.csv
│ ├── food_listings_data.csv
│ ├── providers_data.csv
│ └── receivers_data.csv
├── app.py # Main Streamlit app
├── data_check.py # Data validation
├── data_import.py # Import CSVs into SQLite DB
├── database_setup.py # Setup database schema
├── food_wastage.db # SQLite database
├── requirements.txt # Dependencies
└── README.md # Project documentation

yaml
Copy
Edit

---

## ⚙️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/food-wastage-management.git
   cd food-wastage-management
Create a virtual environment (optional but recommended):

bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # For Linux/Mac
venv\Scripts\activate      # For Windows
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Run the app:

bash
Copy
Edit
streamlit run app.py
