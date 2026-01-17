"""
Services Resource - API endpoints for Insurance, News, Emergency, and Fuel services
"""

from flask import Blueprint, request, jsonify
from utils.insurance import (
    get_insurance_companies, get_company_by_name, estimate_repair_cost,
    get_claim_checklist, get_required_documents, REPAIR_COSTS
)
from utils.news import NewsService, get_traffic_alerts, get_alert_by_id, NEWS_SOURCES
from utils.emergency import (
    get_emergency_numbers, get_hospitals, get_police_stations,
    get_tow_services, get_all_emergency_info
)
from utils.fuel import (
    get_fuel_prices, get_price_history, calculate_trip_cost,
    get_gas_station_chains, get_price_comparison
)

services_bp = Blueprint('services', __name__)


# ============== INSURANCE ENDPOINTS ==============

@services_bp.route('/api/services/insurance/companies', methods=['GET'])
def api_insurance_companies():
    """Get list of all insurance companies in Tunisia"""
    companies = get_insurance_companies()
    return jsonify({
        'success': True,
        'data': companies,
        'count': len(companies)
    })


@services_bp.route('/api/services/insurance/company/<name>', methods=['GET'])
def api_insurance_company(name):
    """Get specific insurance company by name"""
    company = get_company_by_name(name)
    if company:
        return jsonify({'success': True, 'data': company})
    return jsonify({'success': False, 'error': 'Company not found'}), 404


@services_bp.route('/api/services/insurance/estimate', methods=['POST'])
def api_repair_estimate():
    """
    Estimate repair cost based on damage
    
    Request body:
    {
        "parts": ["bumper", "fender", "headlight"],
        "severity": "moderate",  // minor, moderate, severe, critical
        "vehicle_type": "sedan"  // economy, sedan, suv, luxury, truck, motorcycle
    }
    """
    data = request.get_json()
    
    if not data or 'parts' not in data:
        return jsonify({'success': False, 'error': 'Missing parts list'}), 400
    
    parts = data.get('parts', [])
    severity = data.get('severity', 'moderate')
    vehicle_type = data.get('vehicle_type', 'sedan')
    
    estimate = estimate_repair_cost(parts, severity, vehicle_type)
    
    return jsonify({
        'success': True,
        'data': estimate
    })


@services_bp.route('/api/services/insurance/parts', methods=['GET'])
def api_damage_parts():
    """Get list of available damage parts for estimation"""
    parts = [{'id': key, 'name': key.replace('_', ' ').title()} for key in REPAIR_COSTS.keys()]
    return jsonify({
        'success': True,
        'data': parts
    })


@services_bp.route('/api/services/insurance/checklist', methods=['GET'])
def api_claim_checklist():
    """Get insurance claim checklist"""
    return jsonify({
        'success': True,
        'data': get_claim_checklist()
    })


@services_bp.route('/api/services/insurance/documents', methods=['GET'])
def api_required_documents():
    """Get list of required documents for insurance claim"""
    return jsonify({
        'success': True,
        'data': get_required_documents()
    })


# ============== NEWS ENDPOINTS ==============

@services_bp.route('/api/services/news/traffic', methods=['GET'])
def api_traffic_news():
    """Get traffic-related news from various sources"""
    max_items = request.args.get('limit', 20, type=int)
    
    try:
        news = NewsService.get_traffic_news(max_items)
        # Convert datetime to string for JSON
        for item in news:
            if hasattr(item['published'], 'isoformat'):
                item['published'] = item['published'].isoformat()
        
        return jsonify({
            'success': True,
            'data': news,
            'count': len(news)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        })


@services_bp.route('/api/services/news/feed', methods=['GET'])
def api_news_feed():
    """Get all news from Tunisian sources (not just traffic-related)"""
    max_items = request.args.get('limit', 30, type=int)
    
    try:
        news = NewsService.get_all_news(max_items=max_items, traffic_only=False)
        articles = []
        
        for item in news:
            articles.append({
                'id': item['id'],
                'title': item['title'],
                'summary': item['summary'],
                'link': item['link'],
                'source': item['source'],
                'source_type': item.get('source_type', 'news'),
                'published': item['published'].isoformat() if hasattr(item['published'], 'isoformat') else str(item['published']),
                'category': item.get('category', 'general'),
                'location': item.get('location'),
                'is_traffic_related': item.get('is_traffic_related', False)
            })
        
        return jsonify({
            'success': True,
            'articles': articles,
            'count': len(articles),
            'sources': [s['name'] for s in NEWS_SOURCES if s.get('reliable')]
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'articles': []
        })


@services_bp.route('/api/services/news/alerts', methods=['GET'])
def api_traffic_alerts():
    """Get current traffic alerts"""
    governorate = request.args.get('governorate')
    alerts = get_traffic_alerts(governorate)
    
    # Convert datetime to string
    for alert in alerts:
        if hasattr(alert.get('timestamp'), 'isoformat'):
            alert['timestamp'] = alert['timestamp'].isoformat()
    
    return jsonify({
        'success': True,
        'alerts': alerts,
        'count': len(alerts)
    })


@services_bp.route('/api/services/news/alerts/<alert_id>', methods=['GET'])
def api_traffic_alert(alert_id):
    """Get specific traffic alert"""
    alert = get_alert_by_id(alert_id)
    if alert:
        if hasattr(alert.get('timestamp'), 'isoformat'):
            alert['timestamp'] = alert['timestamp'].isoformat()
        return jsonify({'success': True, 'data': alert})
    return jsonify({'success': False, 'error': 'Alert not found'}), 404


# ============== EMERGENCY ENDPOINTS ==============

@services_bp.route('/api/services/emergency/numbers', methods=['GET'])
def api_emergency_numbers():
    """Get all emergency phone numbers"""
    return jsonify({
        'success': True,
        'data': get_emergency_numbers()
    })


@services_bp.route('/api/services/emergency/hospitals', methods=['GET'])
def api_hospitals():
    """Get hospitals, optionally filtered by governorate"""
    governorate = request.args.get('governorate')
    hospitals = get_hospitals(governorate)
    
    return jsonify({
        'success': True,
        'data': hospitals,
        'governorate': governorate or 'all'
    })


@services_bp.route('/api/services/emergency/police', methods=['GET'])
def api_police_stations():
    """Get police stations"""
    governorate = request.args.get('governorate')
    stations = get_police_stations(governorate)
    
    return jsonify({
        'success': True,
        'data': stations
    })


@services_bp.route('/api/services/emergency/tow', methods=['GET'])
def api_tow_services():
    """Get tow truck services"""
    region = request.args.get('region')
    services = get_tow_services(region)
    
    return jsonify({
        'success': True,
        'data': services
    })


@services_bp.route('/api/services/emergency/all', methods=['GET'])
def api_all_emergency():
    """Get comprehensive emergency information"""
    governorate = request.args.get('governorate')
    info = get_all_emergency_info(governorate)
    
    return jsonify({
        'success': True,
        'data': info
    })


# ============== FUEL ENDPOINTS ==============

@services_bp.route('/api/services/fuel/prices', methods=['GET'])
def api_fuel_prices():
    """Get current fuel prices in Tunisia"""
    return jsonify({
        'success': True,
        'data': get_fuel_prices()
    })


@services_bp.route('/api/services/fuel/history', methods=['GET'])
def api_fuel_history():
    """Get historical fuel prices"""
    return jsonify({
        'success': True,
        'data': get_price_history()
    })


@services_bp.route('/api/services/fuel/calculate', methods=['POST'])
def api_trip_cost():
    """
    Calculate fuel cost for a trip
    
    Request body:
    {
        "distance_km": 100,
        "fuel_type": "diesel",
        "consumption_per_100km": 7.0
    }
    """
    data = request.get_json()
    
    if not data or 'distance_km' not in data:
        return jsonify({'success': False, 'error': 'Missing distance'}), 400
    
    result = calculate_trip_cost(
        distance_km=data.get('distance_km', 0),
        fuel_type=data.get('fuel_type', 'diesel'),
        consumption_per_100km=data.get('consumption_per_100km', 7.0)
    )
    
    return jsonify({
        'success': True,
        'data': result
    })


@services_bp.route('/api/services/fuel/stations', methods=['GET'])
def api_gas_stations():
    """Get gas station chains in Tunisia"""
    return jsonify({
        'success': True,
        'data': get_gas_station_chains()
    })


@services_bp.route('/api/services/fuel/compare', methods=['GET'])
def api_price_comparison():
    """Compare fuel prices with regional average"""
    return jsonify({
        'success': True,
        'data': get_price_comparison()
    })


# ============== WEATHER ENDPOINT ==============

@services_bp.route('/api/services/weather', methods=['GET'])
def api_weather():
    """Get current weather for a city/governorate in Tunisia"""
    from utils.weather import WeatherService, WEATHER_RISK
    
    city = request.args.get('city', 'Tunis')
    
    try:
        weather = WeatherService.get_current_weather(city)
        
        if weather:
            # Determine driving risk level
            risk_factor = weather.get('risk_factor', 1.0)
            if risk_factor <= 1.0:
                driving_risk = 'low'
            elif risk_factor <= 1.4:
                driving_risk = 'moderate'
            else:
                driving_risk = 'high'
            
            return jsonify({
                'success': True,
                'city': city,
                'current': {
                    'temperature': weather.get('temperature'),
                    'feels_like': weather.get('feels_like'),
                    'humidity': weather.get('humidity'),
                    'wind_speed': weather.get('windspeed'),
                    'wind_gusts': weather.get('wind_gusts'),
                    'wind_direction': weather.get('winddirection'),
                    'condition': weather.get('weather_description'),
                    'weather_code': weather.get('weathercode'),
                    'precipitation': weather.get('precipitation', 0),
                    'precipitation_probability': weather.get('precipitation_probability', 0),
                    'cloud_cover': weather.get('cloud_cover', 0),
                    'uv_index': weather.get('uv_index', 0),
                    'visibility': 10,  # Default visibility in km
                    'is_day': weather.get('is_day', 1)
                },
                'driving_risk': driving_risk,
                'risk_factor': risk_factor
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unable to fetch weather data'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
