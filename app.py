import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# --- All backend functions (database, prediction) remain the same ---
# (Assuming predictor.py is in the same folder)
from predictor import get_prediction_and_recommendation

DB_FILE = "emission_history.db"

# (init_db, add_to_history, view_history, create_gaps_for_plotting functions are unchanged)
def init_db():
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
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM history", conn)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
    return df

def create_gaps_for_plotting(df, gap_threshold_minutes=30):
    df_with_gaps = df.copy()
    time_diffs = df_with_gaps.index.to_series().diff()
    threshold = pd.Timedelta(minutes=gap_threshold_minutes)
    gap_indices = time_diffs[time_diffs > threshold].index
    for idx in gap_indices:
        nan_timestamp = idx - pd.Timedelta(seconds=1)
        nan_row = pd.DataFrame([[pd.NA]*len(df.columns)], columns=df.columns, index=[nan_timestamp])
        df_with_gaps = pd.concat([df_with_gaps, nan_row])
    return df_with_gaps.sort_index()

init_db()


# --- STREAMLIT DASHBOARD LAYOUT ---
st.set_page_config(layout="wide")
st.title('💡 Household CO₂ Emissions Dashboard')

# --- Sidebar for inputs remains the same ---
st.sidebar.header('Real-Time Simulation')
# ... (all your sliders for weather and appliances are here) ...
temp_c = st.sidebar.slider('Temperature (°C)', -10, 40, 15)
humidity_p = st.sidebar.slider('Humidity (%)', 0, 100, 60)
rain_mm = st.sidebar.slider('Rainfall (mm)', 0, 10, 0)
st.sidebar.header('Live Appliance Data (Watts)')
kettle_w = st.sidebar.slider('Kettle', 0, 2500, 0)
fridge_w = st.sidebar.slider('Fridge-Freezer', 0, 200, 60)
tv_w = st.sidebar.slider('Television', 0, 200, 45)
wm_w = st.sidebar.slider('Washing Machine', 0, 2000, 0)
mw_w = st.sidebar.slider('Microwave', 0, 1500, 0)

live_data = {
    'Fridge-Freezer': fridge_w, 'Washing_Machine': wm_w, 'Dishwasher': 0,
    'Television': tv_w, 'Microwave': mw_w, 'Toaster': 0, 'Hi-Fi': 10,
    'Kettle': kettle_w, 'Oven_Extractor_Fan': 0
}
weather_data = {'temp': temp_c, 'humidity': humidity_p, 'rain': rain_mm}

# --- Main Page ---
# Get all historical data
history_df = view_history()

# --- 1. KPI (Key Performance Indicator) Section ---
st.subheader("Key Metrics")
if 'recommendation' in st.session_state:
    st.info(f"**Recommendation:** {st.session_state.recommendation}")
if not history_df.empty:
    col1, col2, col3 = st.columns(3)
    latest_co2 = history_df['predicted_co2'].iloc[-1]
    avg_co2 = history_df['predicted_co2'].mean()
    max_co2 = history_df['predicted_co2'].max()
    
    col1.metric("Latest Emission (kg CO₂)", f"{latest_co2:.4f}")
    col2.metric("Average Emission (kg CO₂)", f"{avg_co2:.4f}")
    col3.metric("Peak Emission (kg CO₂)", f"{max_co2:.4f}")

# --- 2. Prediction and Recommendation Section ---
if st.sidebar.button('Calculate & Save Emissions'):
    co2, rec = get_prediction_and_recommendation(live_data, temp_c, humidity_p, rain_mm)
    add_to_history(co2, weather_data, live_data)

    # THE FIX: Save the recommendation to the app's memory
    st.session_state.recommendation = rec

    st.rerun()

st.markdown("---") # Visual separator

# --- 3. Historical Data Visualization Section ---
st.subheader('📈 Historical Emissions Analysis')
if history_df.empty:
    st.warning("No historical data yet. Click the button in the sidebar to start tracking.")
else:
    # --- Date Range Selector ---
    min_date = history_df.index.min().date()
    max_date = history_df.index.max().date()
    
    date_range = st.date_input(
        "Select date range to analyze",
        (max_date - timedelta(days=1), max_date), # Default to the last day
        min_value=min_date,
        max_value=max_date,
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
        # Filter the dataframe based on the selected date range
        filtered_df = history_df.loc[str(start_date):str(end_date)]

        st.write(f"Displaying data from **{start_date}** to **{end_date}**")
        plot_df = create_gaps_for_plotting(filtered_df)
        st.line_chart(plot_df['predicted_co2'])

        # --- 4. Deeper Analysis Section ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### Average Emissions by Hour")
            hourly_avg = filtered_df.groupby(filtered_df.index.hour)['predicted_co2'].mean()
            st.bar_chart(hourly_avg)

        with col2:
            st.write("#### Average Emissions by Day of Week")
            # Ensure days are sorted correctly
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            daily_avg = filtered_df.groupby(filtered_df.index.day_name())['predicted_co2'].mean().reindex(days_of_week)
            st.bar_chart(daily_avg)