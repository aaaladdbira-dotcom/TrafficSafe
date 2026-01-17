"""
External Traffic APIs Integration
=================================
Integrates external APIs for traffic-related data:
- Public Holidays (Tunisia)
- Traffic Conditions / Road Status
- News/Alerts related to traffic
"""

import os
import requests
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, List, Dict, Any

# =====================================
# PUBLIC HOLIDAYS API
# =====================================
# Using Nager.Date API (free) - https://date.nager.at/

HOLIDAYS_API_URL = "https://date.nager.at/api/v3"

# Tunisia specific holidays not in international APIs
TUNISIA_HOLIDAYS = {
    2025: [
        {"date": "2025-01-01", "localName": "رأس السنة الميلادية", "name": "New Year's Day", "type": "Public"},
        {"date": "2025-01-14", "localName": "عيد الثورة", "name": "Revolution Day", "type": "Public"},
        {"date": "2025-03-20", "localName": "عيد الاستقلال", "name": "Independence Day", "type": "Public"},
        {"date": "2025-03-29", "localName": "عيد الفطر", "name": "Eid al-Fitr", "type": "Public"},  # Estimated
        {"date": "2025-03-30", "localName": "عيد الفطر", "name": "Eid al-Fitr Day 2", "type": "Public"},
        {"date": "2025-04-09", "localName": "يوم الشهداء", "name": "Martyrs' Day", "type": "Public"},
        {"date": "2025-05-01", "localName": "عيد العمال", "name": "Labour Day", "type": "Public"},
        {"date": "2025-06-05", "localName": "عيد الأضحى", "name": "Eid al-Adha", "type": "Public"},  # Estimated
        {"date": "2025-06-06", "localName": "عيد الأضحى", "name": "Eid al-Adha Day 2", "type": "Public"},
        {"date": "2025-06-26", "localName": "رأس السنة الهجرية", "name": "Islamic New Year", "type": "Public"},
        {"date": "2025-07-25", "localName": "عيد الجمهورية", "name": "Republic Day", "type": "Public"},
        {"date": "2025-08-13", "localName": "يوم المرأة", "name": "Women's Day", "type": "Public"},
        {"date": "2025-09-04", "localName": "المولد النبوي", "name": "Prophet's Birthday", "type": "Public"},
        {"date": "2025-10-15", "localName": "يوم الجلاء", "name": "Evacuation Day", "type": "Public"},
    ],
    2026: [
        {"date": "2026-01-01", "localName": "رأس السنة الميلادية", "name": "New Year's Day", "type": "Public"},
        {"date": "2026-01-14", "localName": "عيد الثورة", "name": "Revolution Day", "type": "Public"},
        {"date": "2026-03-18", "localName": "عيد الفطر", "name": "Eid al-Fitr", "type": "Public"},  # Estimated
        {"date": "2026-03-19", "localName": "عيد الفطر", "name": "Eid al-Fitr Day 2", "type": "Public"},
        {"date": "2026-03-20", "localName": "عيد الاستقلال", "name": "Independence Day", "type": "Public"},
        {"date": "2026-04-09", "localName": "يوم الشهداء", "name": "Martyrs' Day", "type": "Public"},
        {"date": "2026-05-01", "localName": "عيد العمال", "name": "Labour Day", "type": "Public"},
        {"date": "2026-05-25", "localName": "عيد الأضحى", "name": "Eid al-Adha", "type": "Public"},  # Estimated
        {"date": "2026-05-26", "localName": "عيد الأضحى", "name": "Eid al-Adha Day 2", "type": "Public"},
        {"date": "2026-06-16", "localName": "رأس السنة الهجرية", "name": "Islamic New Year", "type": "Public"},
        {"date": "2026-07-25", "localName": "عيد الجمهورية", "name": "Republic Day", "type": "Public"},
        {"date": "2026-08-13", "localName": "يوم المرأة", "name": "Women's Day", "type": "Public"},
        {"date": "2026-08-25", "localName": "المولد النبوي", "name": "Prophet's Birthday", "type": "Public"},
        {"date": "2026-10-15", "localName": "يوم الجلاء", "name": "Evacuation Day", "type": "Public"},
    ]
}

# High traffic impact holidays (higher risk factor)
HIGH_IMPACT_HOLIDAYS = [
    "Eid al-Fitr", "Eid al-Adha", "Independence Day", "Revolution Day", 
    "Republic Day", "New Year's Day"
]


class HolidayService:
    """Service for fetching and managing public holiday data."""
    
    def __init__(self):
        self._cache = {}
        self._cache_time = None
        self._cache_duration = timedelta(hours=24)
    
    def get_tunisia_holidays(self, year: int = None) -> List[Dict[str, Any]]:
        """Get Tunisia public holidays for a specific year.
        
        Uses local data since Nager.Date API doesn't support Tunisia.
        """
        if year is None:
            year = datetime.now().year
        
        holidays = TUNISIA_HOLIDAYS.get(year, [])
        
        # Add risk factor to each holiday
        result = []
        for h in holidays:
            is_high_impact = any(hi in h['name'] for hi in HIGH_IMPACT_HOLIDAYS)
            result.append({
                **h,
                'risk_factor': 1.6 if is_high_impact else 1.3,
                'high_impact': is_high_impact,
                'country': 'TN',
                'country_name': 'Tunisia'
            })
        
        return result
    
    def get_upcoming_holidays(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get holidays in the next N days."""
        today = datetime.now().date()
        end_date = today + timedelta(days=days)
        
        # Get current and next year holidays
        current_year = today.year
        holidays = self.get_tunisia_holidays(current_year)
        if current_year + 1 in TUNISIA_HOLIDAYS:
            holidays.extend(self.get_tunisia_holidays(current_year + 1))
        
        # Filter to upcoming
        upcoming = []
        for h in holidays:
            try:
                h_date = datetime.strptime(h['date'], '%Y-%m-%d').date()
                if today <= h_date <= end_date:
                    days_until = (h_date - today).days
                    upcoming.append({
                        **h,
                        'days_until': days_until,
                        'is_today': days_until == 0,
                        'is_tomorrow': days_until == 1,
                        'is_this_week': days_until <= 7
                    })
            except:
                continue
        
        return sorted(upcoming, key=lambda x: x['date'])
    
    def is_holiday(self, date: datetime = None) -> Dict[str, Any]:
        """Check if a specific date is a holiday."""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        holidays = self.get_tunisia_holidays(date.year)
        
        for h in holidays:
            if h['date'] == date_str:
                return {
                    'is_holiday': True,
                    'holiday': h
                }
        
        return {'is_holiday': False, 'holiday': None}
    
    def get_holiday_risk_factor(self, date: datetime = None) -> float:
        """Get the risk multiplier for accidents on a given date."""
        result = self.is_holiday(date)
        if result['is_holiday']:
            return result['holiday'].get('risk_factor', 1.3)
        
        # Check if it's a day before/after a high-impact holiday
        if date is None:
            date = datetime.now()
        
        for offset in [-1, 1]:  # Day before or after
            check_date = date + timedelta(days=offset)
            check_result = self.is_holiday(check_date)
            if check_result['is_holiday'] and check_result['holiday'].get('high_impact'):
                return 1.25  # Slightly elevated risk
        
        return 1.0


# =====================================
# ROAD CONDITIONS / TRAFFIC STATUS
# =====================================
# Simulated based on typical patterns (Tunisia doesn't have public traffic API)

MAJOR_ROADS = {
    'A1': {'name': 'Autoroute A1', 'from': 'Tunis', 'to': 'Sfax', 'km': 270},
    'A3': {'name': 'Autoroute A3', 'from': 'Tunis', 'to': 'Oued Zarga', 'km': 60},
    'A4': {'name': 'Autoroute A4', 'from': 'Tunis', 'to': 'Bizerte', 'km': 60},
    'RN1': {'name': 'Route Nationale 1', 'from': 'Tunis', 'to': 'Libya Border', 'km': 550},
    'RN3': {'name': 'Route Nationale 3', 'from': 'Tunis', 'to': 'Jendouba', 'km': 150},
    'RN7': {'name': 'Route Nationale 7', 'from': 'Tunis', 'to': 'Kairouan', 'km': 160},
}

# Known accident-prone zones (based on statistics)
HIGH_RISK_ZONES = [
    {'zone': 'Grand Tunis Ring Road', 'governorate': 'Tunis', 'risk_level': 'high', 'reason': 'Heavy traffic'},
    {'zone': 'A1 Sousse Exit', 'governorate': 'Sousse', 'risk_level': 'high', 'reason': 'Merge point'},
    {'zone': 'Sfax Industrial Zone', 'governorate': 'Sfax', 'risk_level': 'medium', 'reason': 'Truck traffic'},
    {'zone': 'Bizerte Port Area', 'governorate': 'Bizerte', 'risk_level': 'medium', 'reason': 'Mixed traffic'},
    {'zone': 'Nabeul Beach Road', 'governorate': 'Nabeul', 'risk_level': 'high', 'reason': 'Tourist season'},
]


class RoadConditionService:
    """Service for road conditions and traffic status."""
    
    def __init__(self):
        self._cache = {}
    
    def get_traffic_status(self, governorate: str = None) -> Dict[str, Any]:
        """Get current traffic status for a governorate or all Tunisia."""
        now = datetime.now()
        hour = now.hour
        is_weekend = now.weekday() >= 5
        
        # Determine traffic level based on time
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            base_level = 'heavy' if not is_weekend else 'moderate'
        elif 10 <= hour <= 16:
            base_level = 'moderate'
        elif 20 <= hour <= 23:
            base_level = 'light'
        else:
            base_level = 'very_light'
        
        # Traffic levels by governorate (simulation)
        gov_factors = {
            'Tunis': 1.5, 'Ariana': 1.3, 'Ben Arous': 1.3,
            'Sfax': 1.2, 'Sousse': 1.2, 'Bizerte': 1.1,
        }
        
        result = {
            'timestamp': now.isoformat(),
            'overall_status': base_level,
            'is_rush_hour': 7 <= hour <= 9 or 17 <= hour <= 19,
            'is_weekend': is_weekend,
            'hour': hour,
            'governorates': []
        }
        
        for gov, factor in gov_factors.items():
            if governorate and gov.lower() != governorate.lower():
                continue
            
            traffic_index = min(100, int(50 * factor * (1 if base_level == 'moderate' else 1.5 if base_level == 'heavy' else 0.5)))
            
            result['governorates'].append({
                'name': gov,
                'traffic_index': traffic_index,
                'status': 'congested' if traffic_index > 70 else 'moderate' if traffic_index > 40 else 'flowing',
                'avg_speed_kmh': max(20, 80 - traffic_index),
                'incidents': 0  # Placeholder
            })
        
        if governorate:
            result['governorates'] = [g for g in result['governorates'] if g['name'].lower() == governorate.lower()]
        
        return result
    
    def get_major_roads(self) -> List[Dict[str, Any]]:
        """Get list of major roads with current status."""
        now = datetime.now()
        hour = now.hour
        
        roads = []
        for road_id, info in MAJOR_ROADS.items():
            # Simulate conditions
            if hour in [7, 8, 17, 18]:
                status = 'busy'
                delay_mins = 15 if 'A1' in road_id else 10
            else:
                status = 'normal'
                delay_mins = 0
            
            roads.append({
                'id': road_id,
                **info,
                'status': status,
                'delay_minutes': delay_mins,
                'avg_speed_kmh': 100 if status == 'normal' else 70,
                'incidents': []
            })
        
        return roads
    
    def get_high_risk_zones(self) -> List[Dict[str, Any]]:
        """Get known high-risk accident zones."""
        return HIGH_RISK_ZONES
    
    def get_road_risk_factor(self, governorate: str = None) -> float:
        """Get risk factor based on current traffic conditions."""
        status = self.get_traffic_status(governorate)
        
        if status['is_rush_hour']:
            return 1.4
        elif status['overall_status'] == 'heavy':
            return 1.3
        elif status['overall_status'] == 'moderate':
            return 1.1
        
        return 1.0


# =====================================
# TRAFFIC NEWS / ALERTS
# =====================================

class TrafficNewsService:
    """Service for traffic news and alerts."""
    
    # Sample alerts for demonstration (in production, integrate with real news API)
    SAMPLE_ALERTS = [
        {
            'id': 1,
            'type': 'road_work',
            'title': 'Road Construction on A1',
            'title_ar': 'أشغال طرقية على الطريق السيارة أ1',
            'description': 'Lane closure between Hammamet and Sousse exits. Expect delays.',
            'governorate': 'Sousse',
            'severity': 'medium',
            'start_date': '2026-01-10',
            'end_date': '2026-01-20',
            'active': True
        },
        {
            'id': 2,
            'type': 'weather_warning',
            'title': 'Heavy Rain Expected',
            'title_ar': 'تحذير من أمطار غزيرة',
            'description': 'Heavy rainfall expected in northern regions. Drive carefully.',
            'governorate': 'Bizerte',
            'severity': 'high',
            'start_date': '2026-01-14',
            'end_date': '2026-01-15',
            'active': True
        },
        {
            'id': 3,
            'type': 'event',
            'title': 'Revolution Day Celebrations',
            'title_ar': 'احتفالات عيد الثورة',
            'description': 'Road closures in central Tunis for national celebrations.',
            'governorate': 'Tunis',
            'severity': 'low',
            'start_date': '2026-01-14',
            'end_date': '2026-01-14',
            'active': True
        }
    ]
    
    def __init__(self):
        self._alerts = self.SAMPLE_ALERTS.copy()
    
    def get_active_alerts(self, governorate: str = None) -> List[Dict[str, Any]]:
        """Get currently active traffic alerts."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        alerts = []
        for alert in self._alerts:
            if not alert['active']:
                continue
            
            if alert['start_date'] <= today <= alert['end_date']:
                if governorate and alert['governorate'].lower() != governorate.lower():
                    continue
                
                alerts.append({
                    **alert,
                    'days_remaining': (datetime.strptime(alert['end_date'], '%Y-%m-%d').date() - 
                                      datetime.now().date()).days
                })
        
        return sorted(alerts, key=lambda x: x['severity'], reverse=True)
    
    def get_alerts_by_type(self, alert_type: str) -> List[Dict[str, Any]]:
        """Get alerts filtered by type (road_work, weather_warning, accident, event)."""
        return [a for a in self.get_active_alerts() if a['type'] == alert_type]
    
    def get_alert_risk_factor(self, governorate: str = None) -> float:
        """Get combined risk factor from active alerts."""
        alerts = self.get_active_alerts(governorate)
        
        if not alerts:
            return 1.0
        
        # Calculate combined factor
        factor = 1.0
        for alert in alerts:
            if alert['severity'] == 'high':
                factor *= 1.3
            elif alert['severity'] == 'medium':
                factor *= 1.15
            else:
                factor *= 1.05
        
        return min(factor, 2.0)  # Cap at 2x


# =====================================
# UNIFIED RISK CALCULATOR
# =====================================

class TrafficRiskCalculator:
    """Unified calculator combining all external factors for risk assessment."""
    
    def __init__(self):
        self.holiday_service = HolidayService()
        self.road_service = RoadConditionService()
        self.news_service = TrafficNewsService()
    
    def get_comprehensive_risk(self, governorate: str = None, date: datetime = None) -> Dict[str, Any]:
        """Get comprehensive risk assessment combining all factors."""
        if date is None:
            date = datetime.now()
        
        # Collect all risk factors
        holiday_factor = self.holiday_service.get_holiday_risk_factor(date)
        road_factor = self.road_service.get_road_risk_factor(governorate)
        alert_factor = self.news_service.get_alert_risk_factor(governorate)
        
        # Time-based factors
        hour = date.hour
        is_night = hour < 6 or hour >= 22
        is_rush_hour = 7 <= hour <= 9 or 17 <= hour <= 19
        is_weekend = date.weekday() >= 5
        
        time_factor = 1.0
        if is_night:
            time_factor = 1.35
        elif is_rush_hour:
            time_factor = 1.25
        
        if is_weekend:
            time_factor *= 1.15
        
        # Combined risk score (0-100)
        combined_factor = holiday_factor * road_factor * alert_factor * time_factor
        risk_score = min(100, int(20 * combined_factor))
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'critical'
        elif risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 30:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Collect contributing factors
        factors = []
        if holiday_factor > 1.0:
            holiday_info = self.holiday_service.is_holiday(date)
            if holiday_info['is_holiday']:
                factors.append({
                    'type': 'holiday',
                    'name': holiday_info['holiday']['name'],
                    'impact': 'high' if holiday_info['holiday'].get('high_impact') else 'medium',
                    'multiplier': holiday_factor
                })
        
        if is_rush_hour:
            factors.append({
                'type': 'rush_hour',
                'name': 'Rush Hour Traffic',
                'impact': 'medium',
                'multiplier': 1.25
            })
        
        if is_night:
            factors.append({
                'type': 'night_driving',
                'name': 'Night Driving',
                'impact': 'high',
                'multiplier': 1.35
            })
        
        alerts = self.news_service.get_active_alerts(governorate)
        for alert in alerts:
            factors.append({
                'type': 'alert',
                'name': alert['title'],
                'impact': alert['severity'],
                'multiplier': 1.3 if alert['severity'] == 'high' else 1.15
            })
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'combined_factor': round(combined_factor, 2),
            'factors': factors,
            'breakdown': {
                'holiday_factor': holiday_factor,
                'road_factor': road_factor,
                'alert_factor': alert_factor,
                'time_factor': round(time_factor, 2)
            },
            'conditions': {
                'is_holiday': holiday_factor > 1.0,
                'is_rush_hour': is_rush_hour,
                'is_night': is_night,
                'is_weekend': is_weekend,
                'active_alerts': len(alerts)
            },
            'timestamp': date.isoformat(),
            'governorate': governorate or 'All Tunisia'
        }


# Singleton instances
holiday_service = HolidayService()
road_service = RoadConditionService()
news_service = TrafficNewsService()
risk_calculator = TrafficRiskCalculator()


# =====================================
# EMERGENCY SERVICES
# =====================================

EMERGENCY_SERVICES = {
    'hospitals': [
        {'id': 'H001', 'name': 'Hôpital Charles Nicolle', 'governorate': 'Tunis', 'type': 'public', 
         'lat': 36.8003, 'lng': 10.1658, 'phone': '71 578 000', 'emergency': True, 'beds': 1400},
        {'id': 'H002', 'name': 'Hôpital La Rabta', 'governorate': 'Tunis', 'type': 'public',
         'lat': 36.8125, 'lng': 10.1547, 'phone': '71 578 788', 'emergency': True, 'beds': 900},
        {'id': 'H003', 'name': 'Hôpital Habib Thameur', 'governorate': 'Tunis', 'type': 'public',
         'lat': 36.7936, 'lng': 10.1814, 'phone': '71 397 000', 'emergency': True, 'beds': 500},
        {'id': 'H004', 'name': 'Hôpital Sahloul', 'governorate': 'Sousse', 'type': 'public',
         'lat': 35.8456, 'lng': 10.6247, 'phone': '73 369 000', 'emergency': True, 'beds': 700},
        {'id': 'H005', 'name': 'Hôpital Fattouma Bourguiba', 'governorate': 'Monastir', 'type': 'public',
         'lat': 35.7643, 'lng': 10.8261, 'phone': '73 461 144', 'emergency': True, 'beds': 650},
        {'id': 'H006', 'name': 'Hôpital Habib Bourguiba', 'governorate': 'Sfax', 'type': 'public',
         'lat': 34.7325, 'lng': 10.7506, 'phone': '74 240 855', 'emergency': True, 'beds': 800},
        {'id': 'H007', 'name': 'Hôpital Régional Bizerte', 'governorate': 'Bizerte', 'type': 'public',
         'lat': 37.2714, 'lng': 9.8639, 'phone': '72 531 400', 'emergency': True, 'beds': 350},
        {'id': 'H008', 'name': 'Hôpital Régional Nabeul', 'governorate': 'Nabeul', 'type': 'public',
         'lat': 36.4561, 'lng': 10.7376, 'phone': '72 285 533', 'emergency': True, 'beds': 300},
        {'id': 'H009', 'name': 'Hôpital Régional Kairouan', 'governorate': 'Kairouan', 'type': 'public',
         'lat': 35.6781, 'lng': 10.0963, 'phone': '77 231 144', 'emergency': True, 'beds': 400},
        {'id': 'H010', 'name': 'Hôpital Régional Gabès', 'governorate': 'Gabes', 'type': 'public',
         'lat': 33.8814, 'lng': 10.0982, 'phone': '75 275 022', 'emergency': True, 'beds': 350},
    ],
    'police_stations': [
        {'id': 'P001', 'name': 'District Police Tunis Centre', 'governorate': 'Tunis', 
         'lat': 36.8065, 'lng': 10.1815, 'phone': '71 340 540', 'type': 'district'},
        {'id': 'P002', 'name': 'Traffic Police HQ', 'governorate': 'Tunis',
         'lat': 36.8103, 'lng': 10.1728, 'phone': '71 341 041', 'type': 'traffic'},
        {'id': 'P003', 'name': 'District Police Sousse', 'governorate': 'Sousse',
         'lat': 35.8256, 'lng': 10.6369, 'phone': '73 225 566', 'type': 'district'},
        {'id': 'P004', 'name': 'District Police Sfax', 'governorate': 'Sfax',
         'lat': 34.7406, 'lng': 10.7603, 'phone': '74 296 300', 'type': 'district'},
        {'id': 'P005', 'name': 'Highway Patrol North', 'governorate': 'Ariana',
         'lat': 36.8667, 'lng': 10.1647, 'phone': '71 708 000', 'type': 'highway'},
    ],
    'fire_stations': [
        {'id': 'F001', 'name': 'Protection Civile Tunis', 'governorate': 'Tunis',
         'lat': 36.8015, 'lng': 10.1825, 'phone': '198', 'response_time_min': 8},
        {'id': 'F002', 'name': 'Protection Civile Sousse', 'governorate': 'Sousse',
         'lat': 35.8288, 'lng': 10.6405, 'phone': '198', 'response_time_min': 10},
        {'id': 'F003', 'name': 'Protection Civile Sfax', 'governorate': 'Sfax',
         'lat': 34.7406, 'lng': 10.7603, 'phone': '198', 'response_time_min': 10},
        {'id': 'F004', 'name': 'Protection Civile Bizerte', 'governorate': 'Bizerte',
         'lat': 37.2744, 'lng': 9.8739, 'phone': '198', 'response_time_min': 12},
    ]
}

EMERGENCY_NUMBERS = {
    'police': '197',
    'ambulance': '190',
    'fire': '198',
    'national_guard': '193',
    'highway_emergency': '71 341 041',
    'traffic_info': '1899'
}


class EmergencyService:
    """Service for emergency services information."""
    
    def get_hospitals(self, governorate: str = None, emergency_only: bool = False) -> List[Dict]:
        """Get list of hospitals, optionally filtered."""
        hospitals = EMERGENCY_SERVICES['hospitals']
        
        if governorate:
            hospitals = [h for h in hospitals if h['governorate'].lower() == governorate.lower()]
        
        if emergency_only:
            hospitals = [h for h in hospitals if h.get('emergency')]
        
        return hospitals
    
    def get_nearest_hospital(self, lat: float, lng: float) -> Dict:
        """Find nearest hospital to given coordinates."""
        import math
        
        def distance(h):
            return math.sqrt((h['lat'] - lat)**2 + (h['lng'] - lng)**2)
        
        hospitals = EMERGENCY_SERVICES['hospitals']
        if not hospitals:
            return None
        
        nearest = min(hospitals, key=distance)
        dist_km = distance(nearest) * 111  # Rough conversion to km
        
        return {
            **nearest,
            'distance_km': round(dist_km, 1),
            'estimated_time_min': round(dist_km * 2, 0)  # Rough estimate
        }
    
    def get_police_stations(self, governorate: str = None, station_type: str = None) -> List[Dict]:
        """Get police stations."""
        stations = EMERGENCY_SERVICES['police_stations']
        
        if governorate:
            stations = [s for s in stations if s['governorate'].lower() == governorate.lower()]
        
        if station_type:
            stations = [s for s in stations if s['type'] == station_type]
        
        return stations
    
    def get_fire_stations(self, governorate: str = None) -> List[Dict]:
        """Get fire stations / civil protection."""
        stations = EMERGENCY_SERVICES['fire_stations']
        
        if governorate:
            stations = [s for s in stations if s['governorate'].lower() == governorate.lower()]
        
        return stations
    
    def get_emergency_numbers(self) -> Dict:
        """Get all emergency contact numbers."""
        return EMERGENCY_NUMBERS
    
    def get_all_services(self, governorate: str = None) -> Dict:
        """Get all emergency services for a location."""
        return {
            'hospitals': self.get_hospitals(governorate),
            'police_stations': self.get_police_stations(governorate),
            'fire_stations': self.get_fire_stations(governorate),
            'emergency_numbers': EMERGENCY_NUMBERS,
            'governorate': governorate or 'All Tunisia'
        }


# =====================================
# SPEED ZONES & LIMITS
# =====================================

SPEED_LIMITS = {
    'highway': {'limit': 110, 'min': 60, 'unit': 'km/h', 'fine_base': 150},
    'expressway': {'limit': 90, 'min': 40, 'unit': 'km/h', 'fine_base': 100},
    'urban': {'limit': 50, 'min': 0, 'unit': 'km/h', 'fine_base': 75},
    'residential': {'limit': 30, 'min': 0, 'unit': 'km/h', 'fine_base': 75},
    'school_zone': {'limit': 20, 'min': 0, 'unit': 'km/h', 'fine_base': 150},
    'construction': {'limit': 30, 'min': 0, 'unit': 'km/h', 'fine_base': 100},
}

SPEED_ZONES = [
    {'id': 'SZ001', 'name': 'A1 Tunis-Sfax', 'type': 'highway', 'governorates': ['Tunis', 'Sousse', 'Sfax']},
    {'id': 'SZ002', 'name': 'A3 Tunis-Oued Zarga', 'type': 'highway', 'governorates': ['Tunis', 'Ben Arous']},
    {'id': 'SZ003', 'name': 'A4 Tunis-Bizerte', 'type': 'highway', 'governorates': ['Tunis', 'Ariana', 'Bizerte']},
    {'id': 'SZ004', 'name': 'Grand Tunis Urban', 'type': 'urban', 'governorates': ['Tunis', 'Ariana', 'Ben Arous', 'Manouba']},
    {'id': 'SZ005', 'name': 'Sousse City Center', 'type': 'urban', 'governorates': ['Sousse']},
    {'id': 'SZ006', 'name': 'Sfax City Center', 'type': 'urban', 'governorates': ['Sfax']},
    {'id': 'SZ007', 'name': 'RN1 National Road', 'type': 'expressway', 'governorates': ['Tunis', 'Nabeul', 'Sousse', 'Sfax', 'Gabes', 'Medenine']},
]


class SpeedZoneService:
    """Service for speed limits and zones."""
    
    def get_speed_limits(self) -> Dict:
        """Get all speed limit categories."""
        return SPEED_LIMITS
    
    def get_speed_zones(self, governorate: str = None, zone_type: str = None) -> List[Dict]:
        """Get speed zones, optionally filtered."""
        zones = []
        
        for zone in SPEED_ZONES:
            if governorate and governorate not in zone['governorates']:
                continue
            if zone_type and zone['type'] != zone_type:
                continue
            
            limit_info = SPEED_LIMITS.get(zone['type'], SPEED_LIMITS['urban'])
            zones.append({
                **zone,
                'speed_limit': limit_info['limit'],
                'min_speed': limit_info['min'],
                'fine_base': limit_info['fine_base']
            })
        
        return zones
    
    def calculate_fine(self, zone_type: str, actual_speed: int) -> Dict:
        """Calculate fine for speeding in a zone."""
        limit_info = SPEED_LIMITS.get(zone_type, SPEED_LIMITS['urban'])
        limit = limit_info['limit']
        
        if actual_speed <= limit:
            return {'violation': False, 'fine': 0, 'points': 0}
        
        over = actual_speed - limit
        base_fine = limit_info['fine_base']
        
        # Calculate fine based on how much over the limit
        if over <= 10:
            fine = base_fine
            points = 1
            severity = 'minor'
        elif over <= 20:
            fine = base_fine * 2
            points = 2
            severity = 'moderate'
        elif over <= 30:
            fine = base_fine * 3
            points = 3
            severity = 'serious'
        else:
            fine = base_fine * 5
            points = 4
            severity = 'severe'
        
        return {
            'violation': True,
            'speed_limit': limit,
            'actual_speed': actual_speed,
            'over_limit': over,
            'fine': fine,
            'fine_currency': 'TND',
            'points': points,
            'severity': severity,
            'license_suspension': over > 40
        }


# =====================================
# VEHICLE & DRIVER INFO
# =====================================

VEHICLE_TYPES = {
    'car': {'name': 'Private Car', 'risk_factor': 1.0, 'avg_occupants': 2.3},
    'motorcycle': {'name': 'Motorcycle', 'risk_factor': 2.8, 'avg_occupants': 1.2},
    'truck': {'name': 'Truck/Lorry', 'risk_factor': 1.5, 'avg_occupants': 1.5},
    'bus': {'name': 'Bus', 'risk_factor': 0.8, 'avg_occupants': 25},
    'taxi': {'name': 'Taxi', 'risk_factor': 1.3, 'avg_occupants': 2.8},
    'louage': {'name': 'Louage (Shared Taxi)', 'risk_factor': 1.4, 'avg_occupants': 7},
    'bicycle': {'name': 'Bicycle', 'risk_factor': 3.2, 'avg_occupants': 1.0},
    'pedestrian': {'name': 'Pedestrian', 'risk_factor': 4.0, 'avg_occupants': 1.0},
}

DRIVER_AGE_RISK = {
    '18-24': {'factor': 1.8, 'description': 'Young driver - higher risk'},
    '25-34': {'factor': 1.2, 'description': 'Early career driver'},
    '35-54': {'factor': 1.0, 'description': 'Experienced driver - lowest risk'},
    '55-64': {'factor': 1.1, 'description': 'Mature driver'},
    '65+': {'factor': 1.4, 'description': 'Senior driver - slower reaction'}
}


class VehicleService:
    """Service for vehicle and driver information."""
    
    def get_vehicle_types(self) -> Dict:
        """Get all vehicle type classifications."""
        return VEHICLE_TYPES
    
    def get_vehicle_risk(self, vehicle_type: str) -> Dict:
        """Get risk assessment for a vehicle type."""
        info = VEHICLE_TYPES.get(vehicle_type, VEHICLE_TYPES['car'])
        return {
            'type': vehicle_type,
            **info,
            'risk_level': 'high' if info['risk_factor'] >= 2.0 else 
                         'medium' if info['risk_factor'] >= 1.3 else 'low'
        }
    
    def get_driver_risk_by_age(self, age: int) -> Dict:
        """Get risk assessment based on driver age."""
        if age < 18:
            return {'error': 'Underage - not licensed'}
        elif age <= 24:
            age_group = '18-24'
        elif age <= 34:
            age_group = '25-34'
        elif age <= 54:
            age_group = '35-54'
        elif age <= 64:
            age_group = '55-64'
        else:
            age_group = '65+'
        
        info = DRIVER_AGE_RISK[age_group]
        return {
            'age': age,
            'age_group': age_group,
            **info,
            'risk_level': 'high' if info['factor'] >= 1.5 else 
                         'medium' if info['factor'] >= 1.2 else 'low'
        }
    
    def calculate_combined_risk(self, vehicle_type: str, driver_age: int, 
                                 conditions: Dict = None) -> Dict:
        """Calculate combined risk score."""
        vehicle_risk = self.get_vehicle_risk(vehicle_type)
        driver_risk = self.get_driver_risk_by_age(driver_age)
        
        base_score = vehicle_risk['risk_factor'] * driver_risk['factor']
        
        # Apply condition modifiers
        if conditions:
            if conditions.get('night'):
                base_score *= 1.3
            if conditions.get('rain'):
                base_score *= 1.4
            if conditions.get('weekend'):
                base_score *= 1.1
            if conditions.get('holiday'):
                base_score *= 1.3
        
        # Normalize to 0-100 scale
        risk_score = min(100, int(base_score * 20))
        
        return {
            'risk_score': risk_score,
            'risk_level': 'critical' if risk_score >= 70 else
                         'high' if risk_score >= 50 else
                         'medium' if risk_score >= 30 else 'low',
            'vehicle': vehicle_risk,
            'driver': driver_risk,
            'base_factor': round(base_score, 2),
            'conditions_applied': conditions or {}
        }


# =====================================
# ROUTE & JOURNEY PLANNING
# =====================================

class RouteService:
    """Service for route risk assessment."""
    
    def __init__(self):
        self.road_service = RoadConditionService()
        self.speed_service = SpeedZoneService()
    
    def assess_route_risk(self, from_gov: str, to_gov: str) -> Dict:
        """Assess risk for a route between governorates."""
        # Get road conditions for both endpoints
        from_status = self.road_service.get_traffic_status(from_gov)
        to_status = self.road_service.get_traffic_status(to_gov)
        
        # Get high risk zones along potential route
        risk_zones = [z for z in HIGH_RISK_ZONES 
                      if z['governorate'] in [from_gov, to_gov]]
        
        # Calculate base risk
        base_risk = 25
        
        # Add traffic-based risk
        from_traffic = next((g['traffic_index'] for g in from_status.get('governorates', []) 
                           if g.get('name') == from_gov), 50)
        to_traffic = next((g['traffic_index'] for g in to_status.get('governorates', []) 
                          if g.get('name') == to_gov), 50)
        traffic_risk = (from_traffic + to_traffic) / 4  # 0-50 contribution
        
        # Add zone-based risk
        zone_risk = len(risk_zones) * 10
        
        total_risk = min(100, int(base_risk + traffic_risk + zone_risk))
        
        return {
            'from': from_gov,
            'to': to_gov,
            'risk_score': total_risk,
            'risk_level': 'high' if total_risk >= 60 else 
                         'medium' if total_risk >= 40 else 'low',
            'traffic_conditions': {
                'origin': from_status.get('overall_status', 'normal'),
                'destination': to_status.get('overall_status', 'normal')
            },
            'risk_zones': risk_zones,
            'recommendations': self._get_recommendations(total_risk, risk_zones)
        }
    
    def _get_recommendations(self, risk_score: int, risk_zones: List) -> List[str]:
        """Get safety recommendations based on risk."""
        recs = []
        
        if risk_score >= 60:
            recs.append("Consider delaying travel if possible")
            recs.append("Allow extra time for your journey")
        
        if risk_score >= 40:
            recs.append("Maintain safe following distance")
            recs.append("Check vehicle condition before departure")
        
        for zone in risk_zones:
            if zone['risk_level'] == 'high':
                recs.append(f"Exercise caution in {zone['zone']} area")
        
        recs.append("Keep emergency numbers handy: Police 197, Ambulance 190")
        
        return recs
    
    def get_journey_stats(self) -> Dict:
        """Get general journey statistics and tips."""
        now = datetime.now()
        hour = now.hour
        
        # Best times to travel
        if 10 <= hour <= 16:
            travel_advisory = 'good'
            advisory_msg = "Good time to travel - low traffic expected"
        elif 7 <= hour <= 9 or 17 <= hour <= 19:
            travel_advisory = 'caution'
            advisory_msg = "Rush hour - expect heavy traffic"
        elif hour >= 22 or hour <= 5:
            travel_advisory = 'warning'
            advisory_msg = "Night driving - increased accident risk"
        else:
            travel_advisory = 'normal'
            advisory_msg = "Normal traffic conditions expected"
        
        return {
            'current_hour': hour,
            'travel_advisory': travel_advisory,
            'advisory_message': advisory_msg,
            'is_rush_hour': 7 <= hour <= 9 or 17 <= hour <= 19,
            'is_night': hour >= 22 or hour <= 5,
            'safest_hours': '10:00 - 16:00',
            'avoid_hours': '07:00-09:00, 17:00-19:00, 22:00-05:00'
        }


# Additional singleton instances
emergency_service = EmergencyService()
speed_service = SpeedZoneService()
vehicle_service = VehicleService()
route_service = RouteService()
