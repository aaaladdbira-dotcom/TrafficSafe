"""
Weather Integration Service
===========================
Correlate accidents with weather conditions
"""

import os
import requests
from datetime import datetime, timedelta
from functools import lru_cache


# Weather API configuration (using Open-Meteo - free, no API key required)
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Tunisia coordinates by governorate
GOVERNORATE_COORDS = {
    'Tunis': (36.8065, 10.1815),
    'Ariana': (36.8667, 10.1647),
    'Ben Arous': (36.7533, 10.2283),
    'Manouba': (36.8078, 9.8589),
    'Nabeul': (36.4561, 10.7376),
    'Zaghouan': (36.4029, 10.1433),
    'Bizerte': (37.2744, 9.8739),
    'Béja': (36.7333, 9.1833),
    'Jendouba': (36.5011, 8.7803),
    'Le Kef': (36.1747, 8.7047),
    'Siliana': (36.0850, 9.3708),
    'Sousse': (35.8288, 10.6405),
    'Monastir': (35.7643, 10.8113),
    'Mahdia': (35.5047, 11.0622),
    'Sfax': (34.7406, 10.7603),
    'Kairouan': (35.6781, 10.0963),
    'Kasserine': (35.1672, 8.8365),
    'Sidi Bouzid': (34.8888, 9.4842),
    'Gabès': (33.8886, 10.0975),
    'Médenine': (33.3549, 10.5055),
    'Tataouine': (32.9297, 10.4518),
    'Gafsa': (34.4250, 8.7842),
    'Tozeur': (33.9197, 8.1339),
    'Kébili': (33.7044, 8.9650),
    # Default (center of Tunisia)
    'default': (34.0, 9.0)
}

# Weather condition codes (WMO codes)
WEATHER_CODES = {
    0: 'Clear sky',
    1: 'Mainly clear',
    2: 'Partly cloudy',
    3: 'Overcast',
    45: 'Fog',
    48: 'Depositing rime fog',
    51: 'Light drizzle',
    53: 'Moderate drizzle',
    55: 'Dense drizzle',
    61: 'Slight rain',
    63: 'Moderate rain',
    65: 'Heavy rain',
    71: 'Slight snow',
    73: 'Moderate snow',
    75: 'Heavy snow',
    80: 'Slight rain showers',
    81: 'Moderate rain showers',
    82: 'Violent rain showers',
    95: 'Thunderstorm',
    96: 'Thunderstorm with slight hail',
    99: 'Thunderstorm with heavy hail'
}

# Risk factors for weather conditions
WEATHER_RISK = {
    0: 0.8,   # Clear - low risk
    1: 0.85,
    2: 0.9,
    3: 1.0,   # Overcast - normal
    45: 1.5,  # Fog - high risk
    48: 1.6,
    51: 1.2,  # Drizzle
    53: 1.3,
    55: 1.4,
    61: 1.3,  # Rain
    63: 1.5,
    65: 1.8,  # Heavy rain - high risk
    71: 1.4,  # Snow
    73: 1.6,
    75: 2.0,  # Heavy snow - very high risk
    80: 1.3,
    81: 1.5,
    82: 1.8,
    95: 1.7,  # Thunderstorm
    96: 2.0,
    99: 2.2   # Thunderstorm with hail - extreme risk
}


class WeatherService:
    """Service for weather data and analysis"""
    
    @staticmethod
    def get_coords(governorate):
        """Get coordinates for a governorate"""
        return GOVERNORATE_COORDS.get(governorate, GOVERNORATE_COORDS['default'])
    
    @staticmethod
    def get_current_weather(governorate='Tunis'):
        """Get current weather for a governorate with full details - NO CACHE for real-time"""
        lat, lon = WeatherService.get_coords(governorate)
        
        try:
            # Fetch current weather with hourly data for more details
            response = requests.get(WEATHER_API_URL, params={
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m,is_day',
                'hourly': 'precipitation_probability,uv_index',
                'timezone': 'Africa/Tunis',
                'forecast_days': 1
            }, timeout=10)
            
            if response.ok:
                data = response.json()
                current = data.get('current', {})
                hourly = data.get('hourly', {})
                
                # Get current hour index for hourly data
                from datetime import datetime
                now = datetime.now()
                current_hour = now.hour
                
                # Get precipitation probability and UV for current hour
                precip_probs = hourly.get('precipitation_probability', [])
                uv_indices = hourly.get('uv_index', [])
                
                precip_prob = precip_probs[current_hour] if current_hour < len(precip_probs) else 0
                uv_index = uv_indices[current_hour] if current_hour < len(uv_indices) else 0
                
                weather_code = current.get('weather_code', 0)
                
                return {
                    'temperature': current.get('temperature_2m'),
                    'feels_like': current.get('apparent_temperature'),
                    'humidity': current.get('relative_humidity_2m'),
                    'precipitation': current.get('precipitation', 0),
                    'rain': current.get('rain', 0),
                    'precipitation_probability': precip_prob,
                    'cloud_cover': current.get('cloud_cover', 0),
                    'windspeed': current.get('wind_speed_10m'),
                    'wind_gusts': current.get('wind_gusts_10m'),
                    'winddirection': current.get('wind_direction_10m'),
                    'weathercode': weather_code,
                    'weather_description': WEATHER_CODES.get(weather_code, 'Unknown'),
                    'is_day': current.get('is_day'),
                    'uv_index': uv_index,
                    'time': current.get('time'),
                    'risk_factor': WEATHER_RISK.get(weather_code, 1.0)
                }
        except Exception as e:
            print(f"Weather API error: {e}")
        
        return None
    
    @staticmethod
    def get_historical_weather(governorate, date):
        """Get historical weather for a specific date"""
        lat, lon = WeatherService.get_coords(governorate)
        
        # Format date
        if isinstance(date, datetime):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = str(date)
        
        try:
            response = requests.get(WEATHER_ARCHIVE_URL, params={
                'latitude': lat,
                'longitude': lon,
                'start_date': date_str,
                'end_date': date_str,
                'daily': 'weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum',
                'timezone': 'Africa/Tunis'
            }, timeout=5)
            
            if response.ok:
                data = response.json()
                daily = data.get('daily', {})
                
                if daily.get('weathercode'):
                    code = daily['weathercode'][0]
                    return {
                        'date': date_str,
                        'weathercode': code,
                        'weather_description': WEATHER_CODES.get(code, 'Unknown'),
                        'temperature_max': daily.get('temperature_2m_max', [None])[0],
                        'temperature_min': daily.get('temperature_2m_min', [None])[0],
                        'precipitation': daily.get('precipitation_sum', [0])[0],
                        'risk_factor': WEATHER_RISK.get(code, 1.0)
                    }
        except Exception as e:
            print(f"Weather archive API error: {e}")
        
        return None
    
    @staticmethod
    def get_weather_forecast(governorate='Tunis', days=7):
        """Get weather forecast"""
        lat, lon = WeatherService.get_coords(governorate)
        
        try:
            response = requests.get(WEATHER_API_URL, params={
                'latitude': lat,
                'longitude': lon,
                'daily': 'weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max',
                'timezone': 'Africa/Tunis',
                'forecast_days': days
            }, timeout=5)
            
            if response.ok:
                data = response.json()
                daily = data.get('daily', {})
                
                forecast = []
                dates = daily.get('time', [])
                codes = daily.get('weathercode', [])
                temp_max = daily.get('temperature_2m_max', [])
                temp_min = daily.get('temperature_2m_min', [])
                precip_prob = daily.get('precipitation_probability_max', [])
                
                for i, date in enumerate(dates):
                    code = codes[i] if i < len(codes) else 0
                    forecast.append({
                        'date': date,
                        'weathercode': code,
                        'weather_description': WEATHER_CODES.get(code, 'Unknown'),
                        'temperature_max': temp_max[i] if i < len(temp_max) else None,
                        'temperature_min': temp_min[i] if i < len(temp_min) else None,
                        'precipitation_probability': precip_prob[i] if i < len(precip_prob) else None,
                        'risk_factor': WEATHER_RISK.get(code, 1.0)
                    })
                
                return forecast
        except Exception as e:
            print(f"Weather forecast API error: {e}")
        
        return []
    
    @staticmethod
    def analyze_accident_weather_correlation(accidents):
        """Analyze correlation between accidents and weather"""
        weather_accident_count = {}
        total_accidents = len(accidents)
        
        for accident in accidents:
            if accident.occurred_at and accident.governorate:
                weather = WeatherService.get_historical_weather(
                    accident.governorate,
                    accident.occurred_at
                )
                if weather:
                    desc = weather['weather_description']
                    weather_accident_count[desc] = weather_accident_count.get(desc, 0) + 1
        
        # Calculate percentages
        correlation = []
        for weather, count in sorted(weather_accident_count.items(), key=lambda x: -x[1]):
            correlation.append({
                'weather': weather,
                'count': count,
                'percentage': round(count / total_accidents * 100, 1) if total_accidents > 0 else 0
            })
        
        return correlation


# Global instance
weather_service = WeatherService()
