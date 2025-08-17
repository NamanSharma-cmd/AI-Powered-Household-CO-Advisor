import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from predictor import get_prediction_and_recommendation # Imports your function

# --- 1. DATABASE SETUP ---
DB_FILE = "emission_history.db"

def init_db():
    """Initializes the SQLite database and creates the history table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history
        (timestamp TEXT, predicted_co2 REAL, temp_c REAL, humidity_p REAL,
         rain_mm REAL, kettle_w REAL, fridge_w REAL, tv_w REAL,
         wm_w REAL, mw_w REAL)
    ''')
    conn.commit()
    conn.close()

def add_to_history(co2, weather_data, appliance_data):
    """Adds a new prediction entry to the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO history VALUES (?,?,?,?,?,?,?,?,?,?)",
              (timestamp, co2, weather_data['temp'], weather_data['humidity'], weather_data['rain'],
               appliance_data['Kettle'], appliance_data['Fridge-Freezer'], appliance_data['Television'],
               appliance_data['Washing_Machine'], appliance_data['Microwave']))
    conn.commit()
    conn.close()

def view_history():
    """Retrieves all historical data from the database and returns it as a DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM history", conn)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
    return df

# --- Initialize the database when the app starts ---
init_db()


# --- 2. STREAMLIT UI ---
st.title('🤖 AI-Powered Household CO₂ Advisor')
st.write("Adjust the sliders to simulate real-time appliance and weather data.")

st.sidebar.header('Current Weather')
temp_c = st.sidebar.slider('Temperature (°C)', -10, 40, 15)
humidity_p = st.sidebar.slider('Humidity (%)', 0, 100, 60)
rain_mm = st.sidebar.slider('Rainfall (mm)', 0, 10, 0)

st.sidebar.header('Live Appliance Data (Watts)')
kettle_w = st.sidebar.slider('Kettle', 0, 2500, 0)
fridge_w = st.sidebar.slider('Fridge-Freezer', 0, 200, 60)
tv_w = st.sidebar.slider('Television', 0, 200, 45)
wm_w = st.sidebar.slider('Washing Machine', 0, 2000, 0)
mw_w = st.sidebar.slider('Microwave', 0, 1500, 0)

# Group appliance and weather data into dictionaries for easier handling
live_data = {
    'Fridge-Freezer': fridge_w, 'Washing_Machine': wm_w, 'Dishwasher': 0,
    'Television': tv_w, 'Microwave': mw_w, 'Toaster': 0, 'Hi-Fi': 10,
    'Kettle': kettle_w, 'Oven_Extractor_Fan': 0
}

weather_data = {'temp': temp_c, 'humidity': humidity_p, 'rain': rain_mm}

# --- 3. PREDICTION AND DATA SAVING ---
if st.button('Calculate & Save Emissions'):
    co2, rec = get_prediction_and_recommendation(live_data, temp_c, humidity_p, rain_mm)
    
    # Save the new entry to the database
    add_to_history(co2, weather_data, live_data)
    
    st.subheader('AI System Output')
    st.metric(label="Predicted CO₂ Emissions (for the next 15 mins)", value=f"{co2:.6f} kg")
    st.info(f"Recommendation: {rec}")

# --- 4. HISTORICAL VIEW ---
st.subheader('📈 Historical Emissions Data')
history_df = view_history()

if history_df.empty:
    st.write("No historical data yet. Click the 'Calculate & Save' button to start tracking.")
else:
    # Display a line chart of the predicted CO2 over time
    st.line_chart(history_df['predicted_co2'])