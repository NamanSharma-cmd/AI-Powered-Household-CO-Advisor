import joblib
import pandas as pd
from datetime import datetime

# --- 1. LOAD THE NEW, UPDATED MODEL ---
model = joblib.load('co2_model_weather.joblib')
print("Weather-aware model loaded successfully.")

def get_prediction_and_recommendation(live_data, temp, humidity, rain):
    """
    Takes live sensor and weather data to make a CO2 prediction.
    """
    
    # --- 2. PREPARE THE DATA FOR THE MODEL ---
    live_df = pd.DataFrame([live_data])
    
    # Add time and new weather features
    now = datetime.now()
    live_df['Hour_of_Day'] = now.hour
    live_df['Day_of_Week'] = now.weekday()
    live_df['Is_Weekend'] = 1 if live_df['Day_of_Week'].iloc[0] >= 5 else 0
    live_df['max_temp °c'] = temp
    live_df['humidity %'] = humidity
    live_df['rain mm'] = rain
    
    # CRITICAL: Ensure the column order is identical to the training script
    feature_order = [
    'Fridge-Freezer', 'Washing_Machine', 'Dishwasher', 'Television',
    'Microwave', 'Toaster', 'Hi-Fi', 'Kettle', 'Oven_Extractor_Fan',
    'Hour_of_Day', 'Day_of_Week', 'Is_Weekend',
    'max_temp °c', 'humidity %', 'rain mm'
]
    live_df = live_df[feature_order]
    
    # --- 3. MAKE A PREDICTION ---
    predicted_co2 = model.predict(live_df)[0]
    
    # --- 4. GENERATE A RECOMMENDATION ---
    recommendation = "Emissions are normal. For consistent savings, consider using high-power appliances during off-peak hours."
    if predicted_co2 > 0.01:
        recommendation = "High emissions detected! This may be due to appliance use or heating/cooling needs based on the weather."
        
    return predicted_co2, recommendation