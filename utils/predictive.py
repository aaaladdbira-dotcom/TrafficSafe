"""
Predictive Analytics Service with AI/ML
========================================
AI-powered accident prediction using machine learning models
"""

from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func, extract
from extensions import db
from models.accident import Accident


class PredictiveAnalytics:
    """AI-powered service for accident prediction and risk analysis"""
    
    def __init__(self):
        self.model_trained = False
        self.feature_cache = None
        self.cache_time = None
    
    def _prepare_training_data(self):
        """Prepare training data from historical accidents for AI model"""
        # Get all accidents with temporal features
        accidents = db.session.query(
            extract('year', Accident.occurred_at).label('year'),
            extract('month', Accident.occurred_at).label('month'),
            extract('day', Accident.occurred_at).label('day_of_month'),
            func.strftime('%w', Accident.occurred_at).label('day_of_week'),
            func.strftime('%H', Accident.occurred_at).label('hour'),
            Accident.severity,
            Accident.governorate,
            func.count(Accident.id).label('count')
        ).filter(
            Accident.occurred_at.isnot(None)
        ).group_by(
            'year', 'month', 'day_of_month', 'day_of_week', 'hour'
        ).all()
        
        return accidents
    
    def _get_day_features(self, date, historical_data=None):
        """Extract features for a given day using historical patterns"""
        day_of_week = date.weekday()
        month = date.month
        day_of_month = date.day
        
        # Use cached historical data or fetch
        if historical_data is None:
            # Get historical accident counts for this day of week
            historical = db.session.query(
                func.count(Accident.id).label('count')
            ).filter(
                func.strftime('%w', Accident.occurred_at) == str((day_of_week + 1) % 7)
            ).scalar() or 0
        else:
            historical = historical_data.get(day_of_week, 0)
        
        # Feature vector
        features = {
            'day_of_week': day_of_week,
            'month': month,
            'day_of_month': day_of_month,
            'is_weekend': 1 if day_of_week >= 5 else 0,
            'is_friday': 1 if day_of_week == 4 else 0,
            'is_summer': 1 if month in [6, 7, 8] else 0,
            'is_winter': 1 if month in [12, 1, 2] else 0,
            'is_month_start': 1 if day_of_month <= 7 else 0,
            'is_month_end': 1 if day_of_month >= 23 else 0,
            'historical_avg': historical
        }
        
        return features
    
    def _calculate_ml_risk_score(self, features, weather_factor=1.0):
        """Calculate risk score using feature-based scoring (simplified ML)"""
        # Base score from historical average
        base_score = min(features['historical_avg'] / 100, 40)
    
    @staticmethod
    def calculate_risk_score(governorate):
        """
        Calculate risk score for a governorate (0-100)
        Based on:
        - Historical accident count
        - Severity distribution
        - Recent trends
        """
        # Get historical data
        total_accidents = Accident.query.filter_by(governorate=governorate).count()
        
        if total_accidents == 0:
            return 0
        
        # Severity weights
        severity_weights = {
            'fatal': 10,
            'severe': 5,
            'moderate': 2,
            'minor': 1
        }
        
        # Calculate weighted severity score
        severity_scores = db.session.query(
            Accident.severity,
            func.count(Accident.id)
        ).filter(
            Accident.governorate == governorate
        ).group_by(Accident.severity).all()
        
        weighted_score = sum(
            severity_weights.get(sev.lower(), 1) * count 
            for sev, count in severity_scores if sev
        )
        
        # Recent trend (last 30 days vs previous 30 days)
        now = datetime.utcnow()
        recent = Accident.query.filter(
            Accident.governorate == governorate,
            Accident.occurred_at >= now - timedelta(days=30)
        ).count()
        
        previous = Accident.query.filter(
            Accident.governorate == governorate,
            Accident.occurred_at >= now - timedelta(days=60),
            Accident.occurred_at < now - timedelta(days=30)
        ).count()
        
        # Trend multiplier
        trend_multiplier = 1.0
        if previous > 0:
            trend_ratio = recent / previous
            if trend_ratio > 1.5:
                trend_multiplier = 1.5  # Increasing trend
            elif trend_ratio > 1.2:
                trend_multiplier = 1.25
            elif trend_ratio < 0.8:
                trend_multiplier = 0.8  # Decreasing trend
        
        # Normalize score to 0-100
        # Base score from weighted severity
        base_score = min(weighted_score / 10, 50)  # Max 50 from severity
        
        # Volume score
        volume_score = min(total_accidents / 100, 30)  # Max 30 from volume
        
        # Recent activity score
        recent_score = min(recent * 2, 20)  # Max 20 from recent activity
        
        final_score = (base_score + volume_score + recent_score) * trend_multiplier
        
        return min(100, max(0, round(final_score)))
    
    @staticmethod
    def get_risk_zones():
        """Get all governorates with risk scores"""
        # Get all governorates with accidents
        governorates = db.session.query(
            Accident.governorate,
            func.count(Accident.id).label('count')
        ).filter(
            Accident.governorate.isnot(None)
        ).group_by(Accident.governorate).all()
        
        risk_zones = []
        for gov, count in governorates:
            if gov:
                risk_score = PredictiveAnalytics.calculate_risk_score(gov)
                risk_level = 'low' if risk_score < 30 else 'medium' if risk_score < 60 else 'high'
                
                risk_zones.append({
                    'governorate': gov,
                    'accident_count': count,
                    'risk_score': risk_score,
                    'risk_level': risk_level
                })
        
        # Sort by risk score descending
        risk_zones.sort(key=lambda x: -x['risk_score'])
        
        return risk_zones
    
    @staticmethod
    def get_high_risk_times():
        """Analyze which times of day have highest accident rates"""
        # Get accident counts by hour
        hourly = db.session.query(
            func.strftime('%H', Accident.occurred_at).label('hour'),
            func.count(Accident.id).label('count')
        ).filter(
            Accident.occurred_at.isnot(None)
        ).group_by('hour').all()
        
        hourly_data = {int(h): c for h, c in hourly if h}
        
        # Find peak hours
        total = sum(hourly_data.values())
        
        results = []
        for hour, count in sorted(hourly_data.items()):
            percentage = (count / total * 100) if total > 0 else 0
            risk_level = 'high' if percentage > 8 else 'medium' if percentage > 5 else 'low'
            
            results.append({
                'hour': hour,
                'display_time': f"{hour:02d}:00 - {(hour+1)%24:02d}:00",
                'count': count,
                'percentage': round(percentage, 1),
                'risk_level': risk_level
            })
        
        return results
    
    @staticmethod
    def get_high_risk_days():
        """Analyze which days of week have highest accident rates"""
        # Get accident counts by day of week
        daily = db.session.query(
            func.strftime('%w', Accident.occurred_at).label('day'),
            func.count(Accident.id).label('count')
        ).filter(
            Accident.occurred_at.isnot(None)
        ).group_by('day').all()
        
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        daily_data = {int(d): c for d, c in daily if d}
        
        total = sum(daily_data.values())
        
        results = []
        for day in range(7):
            count = daily_data.get(day, 0)
            percentage = (count / total * 100) if total > 0 else 0
            # Expected is ~14.3% per day
            risk_level = 'high' if percentage > 18 else 'medium' if percentage > 14 else 'low'
            
            results.append({
                'day': day,
                'day_name': day_names[day],
                'count': count,
                'percentage': round(percentage, 1),
                'risk_level': risk_level
            })
        
        return results
    
    @staticmethod
    def predict_next_week_risk():
        """Predict risk levels for the next 7 days"""
        from utils.weather import weather_service
        
        # Get weather forecast
        forecast = weather_service.get_weather_forecast('Tunis', 7)
        
        # Get historical day-of-week patterns
        day_risks = {d['day']: d['percentage'] for d in PredictiveAnalytics.get_high_risk_days()}
        
        predictions = []
        today = datetime.now()
        
        for i, day_forecast in enumerate(forecast):
            date = today + timedelta(days=i)
            day_of_week = date.weekday()
            # Convert to Sunday=0 format
            day_idx = (day_of_week + 1) % 7
            
            # Base risk from historical patterns
            base_risk = day_risks.get(day_idx, 14.3)
            
            # Weather risk multiplier
            weather_multiplier = day_forecast.get('risk_factor', 1.0)
            
            # Combined risk
            combined_risk = min(100, base_risk * weather_multiplier * 5)  # Scale to 0-100
            
            predictions.append({
                'date': date.strftime('%Y-%m-%d'),
                'day_name': date.strftime('%A'),
                'weather': day_forecast.get('weather_description', 'Unknown'),
                'temperature_max': day_forecast.get('temperature_max'),
                'base_risk': round(base_risk, 1),
                'weather_risk_factor': round(weather_multiplier, 2),
                'predicted_risk': round(combined_risk),
                'risk_level': 'high' if combined_risk > 60 else 'medium' if combined_risk > 40 else 'low'
            })
        
        return predictions
    
    @staticmethod
    def get_cause_predictions():
        """Predict most likely accident causes based on conditions"""
        # Get cause distribution
        causes = db.session.query(
            Accident.cause,
            func.count(Accident.id).label('count')
        ).filter(
            Accident.cause.isnot(None)
        ).group_by(Accident.cause).order_by(func.count(Accident.id).desc()).limit(10).all()
        
        total = sum(c[1] for c in causes)
        
        results = []
        for cause, count in causes:
            percentage = (count / total * 100) if total > 0 else 0
            results.append({
                'cause': cause,
                'count': count,
                'percentage': round(percentage, 1),
                'likelihood': 'very_high' if percentage > 20 else 'high' if percentage > 10 else 'medium' if percentage > 5 else 'low'
            })
        
        return results


# Global instance
predictive = PredictiveAnalytics()
