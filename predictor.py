import joblib
import pandas as pd
from datetime import datetime

model = joblib.load('co2_model_weather.joblib')

def get_prediction_and_recommendation(live_data, temp, humidity, rain):
    """
    Takes live sensor and weather data to make a CO2 prediction and a DYNAMIC recommendation.
    """
    
    # --- Data preparation ---
    live_df = pd.DataFrame([live_data])
    now = datetime.now()
    live_df['Hour_of_Day'] = now.hour
    live_df['Day_of_Week'] = now.weekday()
    live_df['Is_Weekend'] = 1 if live_df['Day_of_Week'].iloc[0] >= 5 else 0
    live_df['max_temp °c'] = temp
    live_df['humidity %'] = humidity
    live_df['rain mm'] = rain
    
    feature_order = [
    'Fridge-Freezer', 'Washing_Machine', 'Dishwasher', 'Television',
    'Microwave', 'Toaster', 'Hi-Fi', 'Kettle', 'Oven_Extractor_Fan',
    'Hour_of_Day', 'Day_of_Week', 'Is_Weekend',
    'max_temp °c', 'humidity %', 'rain mm'
]
    live_df = live_df[feature_order]
    
    predicted_co2 = model.predict(live_df)[0]
    
    # --- Smart Recommendation Logic ---
    recommendation = "Emissions are normal. Great job!"
    
    # Define a threshold for what we consider 'high' emissions
    high_emission_threshold = 0.05 
    
    if predicted_co2 > high_emission_threshold:
        # Identify which high-power appliance is currently on
        high_power_appliances = {k: v for k, v in live_data.items() if v > 400} # Find appliances using >400W
        
        if high_power_appliances:
            # Find the one using the MOST power
            top_appliance = max(high_power_appliances, key=high_power_appliances.get)
            recommendation = f"High emissions detected! The **{top_appliance.replace('_', ' ')}** is the main cause. Consider using it during off-peak hours."
        else:
            # If no single appliance is high, it might be weather or combined usage
            recommendation = "High emissions detected! This may be due to heating/cooling needs or multiple appliances running at once."
            
    return predicted_co2, recommendation