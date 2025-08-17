import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.graph_objects as go # NEW IMPORT
from predictor import get_prediction_and_recommendation

# --- Database functions (init_db, add_to_history, view_history) remain the same ---
DB_FILE = "emission_history.db"

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

# --- NEW PLOTTING FUNCTION USING PLOTLY ---
def create_custom_line_chart(df, gap_threshold_minutes=30):
    """Creates a Plotly line chart with dotted lines across large gaps."""
    fig = go.Figure()
    
    if df.empty:
        return fig # Return an empty figure if no data

    # Find the gaps
    time_diffs = df.index.to_series().diff()
    threshold = pd.Timedelta(minutes=gap_threshold_minutes)
    
    # Split data into continuous segments
    segments = []
    current_segment_start = df.index[0]
    
    for i in range(1, len(df)):
        if time_diffs.iloc[i] > threshold:
            # End of a segment
            segments.append(df.loc[current_segment_start:time_diffs.index[i-1]])
            current_segment_start = df.index[i]
    # Add the last segment
    segments.append(df.loc[current_segment_start:])

    # Plot each segment
    for i, segment in enumerate(segments):
        # Plot the continuous data with a solid line
        fig.add_trace(go.Scatter(
            x=segment.index, y=segment['predicted_co2'], mode='lines',
            line=dict(color='deepskyblue', width=2), name='Emission Data',
            showlegend=(i == 0) # Only show legend for the first segment
        ))
        
        # If it's not the last segment, add a dotted line to the next one
        if i < len(segments) - 1:
            next_segment = segments[i+1]
            gap_start_x = segment.index[-1]
            gap_start_y = segment['predicted_co2'].iloc[-1]
            gap_end_x = next_segment.index[0]
            gap_end_y = next_segment['predicted_co2'].iloc[0]
            
            fig.add_trace(go.Scatter(
                x=[gap_start_x, gap_end_x], y=[gap_start_y, gap_end_y], mode='lines',
                line=dict(color='deepskyblue', width=1, dash='dot'),
                showlegend=False
            ))
            
    # Update layout for a clean look
    fig.update_layout(
        title='Historical Emissions Data',
        xaxis_title='Time',
        yaxis_title='CO2 (kg)',
        template='plotly_dark' # Use a dark theme like the default chart
    )
    return fig


# --- STREAMLIT DASHBOARD LAYOUT (Main part is unchanged) ---
st.set_page_config(layout="wide")
st.title('💡 Household CO₂ Emissions Dashboard')
st.sidebar.header('Real-Time Simulation')
# ... (all your sliders) ...
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
if st.sidebar.button('Calculate & Save Emissions'):
    co2, rec = get_prediction_and_recommendation(live_data, temp_c, humidity_p, rain_mm)
    add_to_history(co2, weather_data, live_data)
    st.session_state.recommendation = rec
    st.rerun()

st.subheader("Key Metrics")
history_df = view_history()
if not history_df.empty:
    # ... (KPI metrics columns) ...
    col1, col2, col3 = st.columns(3)
    latest_co2 = history_df['predicted_co2'].iloc[-1]
    avg_co2 = history_df['predicted_co2'].mean()
    max_co2 = history_df['predicted_co2'].max()
    col1.metric("Latest Emission (kg CO₂)", f"{latest_co2:.4f}")
    col2.metric("Average Emission (kg CO₂)", f"{avg_co2:.4f}")
    col3.metric("Peak Emission (kg CO₂)", f"{max_co2:.4f}")
if 'recommendation' in st.session_state:
    st.info(f"**Recommendation:** {st.session_state.recommendation}")
st.markdown("---")

# --- HISTORICAL DATA VISUALIZATION SECTION ---
st.subheader('📈 Historical Emissions Analysis')
if history_df.empty:
    st.warning("No historical data yet. Click the button in the sidebar to start tracking.")
else:
    # --- THIS IS THE UPDATED PLOTTING LOGIC ---
    # Create and display the custom Plotly chart
    fig = create_custom_line_chart(history_df)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View Raw Historical Data"):
        st.dataframe(history_df)