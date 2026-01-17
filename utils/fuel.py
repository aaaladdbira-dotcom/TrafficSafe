"""
Fuel Price Service for Tunisia
==============================
Current fuel prices and historical data
"""

import requests
from datetime import datetime, timedelta
from functools import lru_cache

# Current fuel prices in Tunisia (TND per liter) - Updated regularly
# These are official prices set by the government
CURRENT_FUEL_PRICES = {
    'updated': '2026-01-15',
    'currency': 'TND',
    'unit': 'liter',
    'prices': {
        'essence_super': {
            'name': 'Super (Essence)',
            'name_fr': 'Super Sans Plomb',
            'name_ar': 'بنزين سوبر',
            'price': 2.525,
            'icon': '⛽',
            'color': '#ef4444'
        },
        'essence_normal': {
            'name': 'Regular (Essence)',
            'name_fr': 'Essence Normale',
            'name_ar': 'بنزين عادي',
            'price': 2.345,
            'icon': '⛽',
            'color': '#f97316'
        },
        'diesel': {
            'name': 'Diesel (Gasoil)',
            'name_fr': 'Gasoil',
            'name_ar': 'ديزل',
            'price': 2.025,
            'icon': '🛢️',
            'color': '#eab308'
        },
        'diesel_premium': {
            'name': 'Diesel Premium',
            'name_fr': 'Gasoil 50',
            'name_ar': 'ديزل ممتاز',
            'price': 2.165,
            'icon': '🛢️',
            'color': '#84cc16'
        },
        'gpl': {
            'name': 'LPG (GPL)',
            'name_fr': 'GPL Carburant',
            'name_ar': 'غاز البترول المسال',
            'price': 0.895,
            'icon': '🔥',
            'color': '#22c55e'
        }
    }
}

# Price history (for trend analysis)
PRICE_HISTORY = [
    {'date': '2024-01-01', 'essence_super': 2.255, 'diesel': 1.865},
    {'date': '2024-04-01', 'essence_super': 2.325, 'diesel': 1.905},
    {'date': '2024-07-01', 'essence_super': 2.395, 'diesel': 1.945},
    {'date': '2024-10-01', 'essence_super': 2.455, 'diesel': 1.985},
    {'date': '2025-01-01', 'essence_super': 2.485, 'diesel': 2.005},
    {'date': '2025-04-01', 'essence_super': 2.495, 'diesel': 2.015},
    {'date': '2025-07-01', 'essence_super': 2.505, 'diesel': 2.020},
    {'date': '2025-10-01', 'essence_super': 2.515, 'diesel': 2.022},
    {'date': '2026-01-01', 'essence_super': 2.525, 'diesel': 2.025},
]


def get_fuel_prices():
    """Get current fuel prices"""
    return CURRENT_FUEL_PRICES


def get_price_history():
    """Get historical fuel prices"""
    return PRICE_HISTORY


def calculate_trip_cost(distance_km, fuel_type='diesel', consumption_per_100km=7.0):
    """
    Calculate estimated fuel cost for a trip
    
    Args:
        distance_km: Distance in kilometers
        fuel_type: Type of fuel (essence_super, essence_normal, diesel, diesel_premium, gpl)
        consumption_per_100km: Vehicle fuel consumption (liters per 100km)
    
    Returns:
        dict with cost breakdown
    """
    prices = CURRENT_FUEL_PRICES['prices']
    
    if fuel_type not in prices:
        fuel_type = 'diesel'
    
    price_per_liter = prices[fuel_type]['price']
    fuel_needed = (distance_km / 100) * consumption_per_100km
    total_cost = fuel_needed * price_per_liter
    
    return {
        'distance_km': distance_km,
        'fuel_type': prices[fuel_type]['name'],
        'consumption_per_100km': consumption_per_100km,
        'fuel_needed_liters': round(fuel_needed, 2),
        'price_per_liter': price_per_liter,
        'total_cost': round(total_cost, 2),
        'currency': 'TND'
    }


# Gas stations (major chains)
GAS_STATION_CHAINS = [
    {
        'name': 'AGIL',
        'logo': 'agil',
        'stations_count': 320,
        'coverage': 'National',
        'services': ['fuel', 'shop', 'car_wash', 'air']
    },
    {
        'name': 'Shell',
        'logo': 'shell', 
        'stations_count': 180,
        'coverage': 'National',
        'services': ['fuel', 'shop', 'premium_fuel']
    },
    {
        'name': 'Total Energies',
        'logo': 'total',
        'stations_count': 150,
        'coverage': 'National',
        'services': ['fuel', 'shop', 'car_wash', 'restaurant']
    },
    {
        'name': 'Oilibya',
        'logo': 'oilibya',
        'stations_count': 120,
        'coverage': 'National',
        'services': ['fuel', 'shop']
    },
    {
        'name': 'SNDP',
        'logo': 'sndp',
        'stations_count': 100,
        'coverage': 'National',
        'services': ['fuel', 'shop']
    }
]


def get_gas_station_chains():
    """Get list of gas station chains in Tunisia"""
    return GAS_STATION_CHAINS


def get_price_comparison():
    """Compare current prices with regional average"""
    # Regional comparison (North Africa average)
    regional_avg = {
        'essence_super': 2.15,  # Regional average
        'diesel': 1.85
    }
    
    current = CURRENT_FUEL_PRICES['prices']
    
    return {
        'tunisia': {
            'essence_super': current['essence_super']['price'],
            'diesel': current['diesel']['price']
        },
        'regional_average': regional_avg,
        'difference': {
            'essence_super': round(current['essence_super']['price'] - regional_avg['essence_super'], 3),
            'diesel': round(current['diesel']['price'] - regional_avg['diesel'], 3)
        }
    }
