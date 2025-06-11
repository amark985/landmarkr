import requests
from env.config import OPEN_WEATHER_API_KEY

def get_current_weather(lat, lon, units="imperial"):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPEN_WEATHER_API_KEY}&units={units}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_forecast_weather(lat, lon, units="imperial"):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPEN_WEATHER_API_KEY}&units={units}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


