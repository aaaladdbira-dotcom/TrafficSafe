"""
Emergency Services for Tunisia
==============================
Emergency contacts, hospital locations, and services
"""

# National Emergency Numbers
EMERGENCY_NUMBERS = {
    'police': {'number': '197', 'name': 'Police', 'icon': '👮'},
    'ambulance': {'number': '190', 'name': 'SAMU (Emergency Medical)', 'icon': '🚑'},
    'fire': {'number': '198', 'name': 'Fire Department', 'icon': '🚒'},
    'national_guard': {'number': '193', 'name': 'National Guard', 'icon': '🛡️'},
    'traffic_police': {'number': '71 341 141', 'name': 'Traffic Police', 'icon': '🚔'},
    'civil_protection': {'number': '71 560 006', 'name': 'Civil Protection', 'icon': '⛑️'},
}

# Major Hospitals by Governorate
HOSPITALS = {
    'Tunis': [
        {
            'name': 'Hôpital Charles Nicolle',
            'address': 'Boulevard du 9 Avril 1938, Tunis',
            'phone': '71 578 000',
            'type': 'Public',
            'emergency': True,
            'coords': (36.8003, 10.1658)
        },
        {
            'name': 'Hôpital La Rabta',
            'address': 'Jebel Lakhdar, Tunis',
            'phone': '71 578 788',
            'type': 'Public',
            'emergency': True,
            'coords': (36.8089, 10.1547)
        },
        {
            'name': 'Clinique El Manar',
            'address': 'El Manar, Tunis',
            'phone': '71 888 000',
            'type': 'Private',
            'emergency': True,
            'coords': (36.8425, 10.1506)
        },
        {
            'name': 'Clinique Les Berges du Lac',
            'address': 'Les Berges du Lac, Tunis',
            'phone': '71 961 900',
            'type': 'Private',
            'emergency': True,
            'coords': (36.8344, 10.2306)
        },
        {
            'name': 'Hôpital Militaire',
            'address': 'Montfleury, Tunis',
            'phone': '71 391 133',
            'type': 'Military',
            'emergency': True,
            'coords': (36.7933, 10.1797)
        }
    ],
    'Sfax': [
        {
            'name': 'Hôpital Habib Bourguiba',
            'address': 'Route El Ain, Sfax',
            'phone': '74 241 511',
            'type': 'Public',
            'emergency': True,
            'coords': (34.7456, 10.7617)
        },
        {
            'name': 'Hôpital Hédi Chaker',
            'address': 'Route de Tunis, Sfax',
            'phone': '74 242 411',
            'type': 'Public',
            'emergency': True,
            'coords': (34.7589, 10.7722)
        },
        {
            'name': 'Clinique El Yosr',
            'address': 'Route de Gabes, Sfax',
            'phone': '74 276 444',
            'type': 'Private',
            'emergency': True,
            'coords': (34.7234, 10.7689)
        }
    ],
    'Sousse': [
        {
            'name': 'Hôpital Farhat Hached',
            'address': 'Avenue Ibn El Jazzar, Sousse',
            'phone': '73 221 411',
            'type': 'Public',
            'emergency': True,
            'coords': (35.8256, 10.6089)
        },
        {
            'name': 'Hôpital Sahloul',
            'address': 'Sahloul, Sousse',
            'phone': '73 369 000',
            'type': 'Public',
            'emergency': True,
            'coords': (35.8567, 10.5953)
        },
        {
            'name': 'Clinique Les Oliviers',
            'address': 'Boulevard 14 Janvier, Sousse',
            'phone': '73 242 700',
            'type': 'Private',
            'emergency': True,
            'coords': (35.8289, 10.6134)
        }
    ],
    'Bizerte': [
        {
            'name': 'Hôpital Régional de Bizerte',
            'address': 'Route de Tunis, Bizerte',
            'phone': '72 431 522',
            'type': 'Public',
            'emergency': True,
            'coords': (37.2744, 9.8639)
        },
        {
            'name': 'Hôpital Habib Bougatfa',
            'address': 'Bizerte',
            'phone': '72 590 000',
            'type': 'Public',
            'emergency': True,
            'coords': (37.2678, 9.8767)
        }
    ],
    'Gabès': [
        {
            'name': 'Hôpital Régional de Gabès',
            'address': 'Gabès Centre',
            'phone': '75 270 400',
            'type': 'Public',
            'emergency': True,
            'coords': (33.8886, 10.0975)
        }
    ],
    'Kairouan': [
        {
            'name': 'Hôpital Ibn El Jazzar',
            'address': 'Kairouan',
            'phone': '77 227 411',
            'type': 'Public',
            'emergency': True,
            'coords': (35.6781, 10.0963)
        }
    ],
    'Nabeul': [
        {
            'name': 'Hôpital Mohamed Taher Maamouri',
            'address': 'Nabeul',
            'phone': '72 285 633',
            'type': 'Public',
            'emergency': True,
            'coords': (36.4561, 10.7376)
        },
        {
            'name': 'Hôpital de Hammamet',
            'address': 'Hammamet',
            'phone': '72 280 572',
            'type': 'Public',
            'emergency': True,
            'coords': (36.4008, 10.6167)
        }
    ],
    'Monastir': [
        {
            'name': 'Hôpital Fattouma Bourguiba',
            'address': 'Monastir',
            'phone': '73 461 144',
            'type': 'Public',
            'emergency': True,
            'coords': (35.7643, 10.8113)
        }
    ]
}

# Police Stations by Governorate
POLICE_STATIONS = {
    'Tunis': [
        {'name': 'Central Police Station', 'address': 'Avenue Habib Bourguiba', 'phone': '71 341 141'},
        {'name': 'Bab Bhar Police Station', 'address': 'Place de Barcelone', 'phone': '71 256 633'},
        {'name': 'El Menzah Police Station', 'address': 'El Menzah 6', 'phone': '71 232 199'},
    ],
    'Sfax': [
        {'name': 'Central Police Station', 'address': 'Centre Ville', 'phone': '74 211 100'},
    ],
    'Sousse': [
        {'name': 'Central Police Station', 'address': 'Centre Ville', 'phone': '73 225 566'},
    ]
}

# Tow Truck Services (24/7)
TOW_SERVICES = [
    {
        'name': 'SOS Dépannage Tunisie',
        'phone': '71 862 862',
        'coverage': 'National',
        'available_24h': True
    },
    {
        'name': 'Touring Club de Tunisie (TCT)',
        'phone': '71 323 152',
        'coverage': 'National',
        'available_24h': True
    },
    {
        'name': 'Auto Assistance',
        'phone': '71 780 780',
        'coverage': 'Greater Tunis',
        'available_24h': True
    },
    {
        'name': 'Dépannage Express Sfax',
        'phone': '74 400 400',
        'coverage': 'Sfax Region',
        'available_24h': True
    },
    {
        'name': 'SOS Auto Sousse',
        'phone': '73 300 300',
        'coverage': 'Sahel Region',
        'available_24h': True
    }
]


def get_emergency_numbers():
    """Get all emergency phone numbers"""
    return EMERGENCY_NUMBERS


def get_hospitals(governorate=None):
    """Get hospitals, optionally filtered by governorate"""
    if governorate:
        return HOSPITALS.get(governorate, [])
    return HOSPITALS


def get_nearest_hospital(governorate):
    """Get hospitals in a specific governorate"""
    return HOSPITALS.get(governorate, HOSPITALS.get('Tunis', []))


def get_police_stations(governorate=None):
    """Get police stations"""
    if governorate:
        return POLICE_STATIONS.get(governorate, [])
    return POLICE_STATIONS


def get_tow_services(region=None):
    """Get tow truck services"""
    if region:
        return [s for s in TOW_SERVICES if region.lower() in s['coverage'].lower() or s['coverage'] == 'National']
    return TOW_SERVICES


def get_all_emergency_info(governorate=None):
    """Get comprehensive emergency information"""
    return {
        'emergency_numbers': get_emergency_numbers(),
        'hospitals': get_nearest_hospital(governorate) if governorate else HOSPITALS.get('Tunis', []),
        'tow_services': get_tow_services(),
        'governorate': governorate or 'Tunis'
    }
