"""
Insurance Services for Tunisia
==============================
Insurance company data, cost estimation, and claim guidance
"""

# Tunisian Insurance Companies (Real data)
INSURANCE_COMPANIES = [
    {
        'name': 'STAR (Société Tunisienne d\'Assurances et de Réassurances)',
        'phone': '71 340 866',
        'website': 'www.star.com.tn',
        'email': 'contact@star.com.tn',
        'address': 'Tunis',
        'type': 'Public',
        'rating': 4.2,
        'claim_time_days': 15,
        'logo': 'star'
    },
    {
        'name': 'GAT Assurances',
        'phone': '71 861 000',
        'website': 'www.gat.com.tn',
        'email': 'contact@gat.com.tn',
        'address': 'Tunis',
        'type': 'Private',
        'rating': 4.0,
        'claim_time_days': 12,
        'logo': 'gat'
    },
    {
        'name': 'COMAR (Compagnie Méditerranéenne d\'Assurances)',
        'phone': '71 833 000',
        'website': 'www.comar.com.tn',
        'email': 'info@comar.com.tn',
        'address': 'Tunis',
        'type': 'Private',
        'rating': 4.1,
        'claim_time_days': 14,
        'logo': 'comar'
    },
    {
        'name': 'Assurances MAGHREBIA',
        'phone': '71 789 200',
        'website': 'www.maghrebia.com.tn',
        'email': 'contact@maghrebia.com.tn',
        'address': 'Tunis',
        'type': 'Private',
        'rating': 3.9,
        'claim_time_days': 18,
        'logo': 'maghrebia'
    },
    {
        'name': 'CARTE Assurances',
        'phone': '71 792 000',
        'website': 'www.carte.com.tn',
        'email': 'info@carte.com.tn',
        'address': 'Tunis',
        'type': 'Private',
        'rating': 4.0,
        'claim_time_days': 10,
        'logo': 'carte'
    },
    {
        'name': 'ASTREE Assurances',
        'phone': '71 167 500',
        'website': 'www.astree.com.tn',
        'email': 'contact@astree.com.tn',
        'address': 'Tunis',
        'type': 'Private',
        'rating': 4.3,
        'claim_time_days': 11,
        'logo': 'astree'
    },
    {
        'name': 'AMI Assurances',
        'phone': '71 285 700',
        'website': 'www.ami.com.tn',
        'email': 'contact@ami.com.tn',
        'address': 'Tunis',
        'type': 'Private',
        'rating': 3.8,
        'claim_time_days': 16,
        'logo': 'ami'
    },
    {
        'name': 'BH Assurance',
        'phone': '71 126 000',
        'website': 'www.bhassurance.com.tn',
        'email': 'info@bhassurance.com.tn',
        'address': 'Tunis',
        'type': 'Bank-Insurance',
        'rating': 4.0,
        'claim_time_days': 13,
        'logo': 'bh'
    },
    {
        'name': 'LLOYD Assurances',
        'phone': '71 842 600',
        'website': 'www.lloyd.com.tn',
        'email': 'contact@lloyd.com.tn',
        'address': 'Tunis',
        'type': 'Private',
        'rating': 3.7,
        'claim_time_days': 20,
        'logo': 'lloyd'
    },
    {
        'name': 'SALIM Assurances',
        'phone': '71 940 600',
        'website': 'www.salim-assurances.com',
        'email': 'info@salim-assurances.com',
        'address': 'Tunis',
        'type': 'Private',
        'rating': 3.6,
        'claim_time_days': 17,
        'logo': 'salim'
    }
]

# Average repair costs in Tunisia (in TND - Tunisian Dinar)
REPAIR_COSTS = {
    'bumper': {'min': 150, 'max': 800, 'avg': 400},
    'fender': {'min': 200, 'max': 1000, 'avg': 500},
    'door': {'min': 400, 'max': 2000, 'avg': 1000},
    'hood': {'min': 300, 'max': 1500, 'avg': 700},
    'trunk': {'min': 300, 'max': 1200, 'avg': 600},
    'windshield': {'min': 200, 'max': 800, 'avg': 450},
    'side_mirror': {'min': 100, 'max': 500, 'avg': 250},
    'headlight': {'min': 150, 'max': 600, 'avg': 350},
    'taillight': {'min': 100, 'max': 400, 'avg': 200},
    'paint_panel': {'min': 200, 'max': 600, 'avg': 350},
    'frame_damage': {'min': 1500, 'max': 8000, 'avg': 4000},
    'suspension': {'min': 400, 'max': 2000, 'avg': 1000},
    'airbag': {'min': 800, 'max': 2500, 'avg': 1500},
    'engine_minor': {'min': 500, 'max': 3000, 'avg': 1500},
    'engine_major': {'min': 3000, 'max': 15000, 'avg': 8000},
    'total_loss': {'min': 10000, 'max': 50000, 'avg': 25000}
}

# Severity multipliers
SEVERITY_MULTIPLIERS = {
    'minor': 0.7,      # Scratches, small dents
    'moderate': 1.0,   # Visible damage, functional
    'severe': 1.5,     # Major damage, drivable
    'critical': 2.0    # Extensive damage, not drivable
}

# Vehicle type multipliers
VEHICLE_MULTIPLIERS = {
    'economy': 0.8,
    'sedan': 1.0,
    'suv': 1.3,
    'luxury': 2.0,
    'truck': 1.2,
    'motorcycle': 0.6
}


def get_insurance_companies():
    """Get list of all insurance companies"""
    return INSURANCE_COMPANIES


def get_company_by_name(name):
    """Get specific insurance company by name"""
    for company in INSURANCE_COMPANIES:
        if name.lower() in company['name'].lower():
            return company
    return None


def estimate_repair_cost(damage_parts, severity='moderate', vehicle_type='sedan'):
    """
    Estimate total repair cost based on damaged parts
    
    Args:
        damage_parts: list of damaged parts (e.g., ['bumper', 'fender', 'headlight'])
        severity: 'minor', 'moderate', 'severe', 'critical'
        vehicle_type: 'economy', 'sedan', 'suv', 'luxury', 'truck', 'motorcycle'
    
    Returns:
        dict with cost breakdown
    """
    severity_mult = SEVERITY_MULTIPLIERS.get(severity, 1.0)
    vehicle_mult = VEHICLE_MULTIPLIERS.get(vehicle_type, 1.0)
    
    breakdown = []
    total_min = 0
    total_max = 0
    total_avg = 0
    
    for part in damage_parts:
        if part in REPAIR_COSTS:
            cost = REPAIR_COSTS[part]
            adjusted_min = int(cost['min'] * severity_mult * vehicle_mult)
            adjusted_max = int(cost['max'] * severity_mult * vehicle_mult)
            adjusted_avg = int(cost['avg'] * severity_mult * vehicle_mult)
            
            breakdown.append({
                'part': part.replace('_', ' ').title(),
                'min': adjusted_min,
                'max': adjusted_max,
                'avg': adjusted_avg
            })
            
            total_min += adjusted_min
            total_max += adjusted_max
            total_avg += adjusted_avg
    
    # Add labor cost (20-30% of parts)
    labor_min = int(total_min * 0.2)
    labor_max = int(total_max * 0.3)
    labor_avg = int(total_avg * 0.25)
    
    return {
        'parts_breakdown': breakdown,
        'parts_total': {
            'min': total_min,
            'max': total_max,
            'avg': total_avg
        },
        'labor': {
            'min': labor_min,
            'max': labor_max,
            'avg': labor_avg
        },
        'grand_total': {
            'min': total_min + labor_min,
            'max': total_max + labor_max,
            'avg': total_avg + labor_avg
        },
        'severity': severity,
        'vehicle_type': vehicle_type,
        'currency': 'TND'
    }


# Insurance claim checklist
CLAIM_CHECKLIST = {
    'at_scene': [
        {'id': 1, 'text': 'Ensure everyone\'s safety and call emergency services if needed', 'icon': '🚨'},
        {'id': 2, 'text': 'Take photos of all vehicles involved and damage', 'icon': '📸'},
        {'id': 3, 'text': 'Take photos of the accident scene, road conditions, and signs', 'icon': '🛣️'},
        {'id': 4, 'text': 'Exchange information with other drivers (name, phone, insurance)', 'icon': '📝'},
        {'id': 5, 'text': 'Get contact information from witnesses', 'icon': '👥'},
        {'id': 6, 'text': 'Note the exact time and location of the accident', 'icon': '📍'},
        {'id': 7, 'text': 'Do NOT admit fault or sign any documents', 'icon': '⚠️'},
    ],
    'within_24h': [
        {'id': 8, 'text': 'File a police report (Procès-verbal)', 'icon': '👮'},
        {'id': 9, 'text': 'Notify your insurance company', 'icon': '📞'},
        {'id': 10, 'text': 'Fill out the accident report form (Constat amiable)', 'icon': '📋'},
        {'id': 11, 'text': 'Get a medical examination if injured', 'icon': '🏥'},
    ],
    'claim_process': [
        {'id': 12, 'text': 'Submit claim form with all documentation', 'icon': '📤'},
        {'id': 13, 'text': 'Provide photos and police report', 'icon': '🖼️'},
        {'id': 14, 'text': 'Get repair estimates from approved garages', 'icon': '🔧'},
        {'id': 15, 'text': 'Attend expert assessment if required', 'icon': '👨‍💼'},
        {'id': 16, 'text': 'Follow up regularly on claim status', 'icon': '📊'},
    ]
}


def get_claim_checklist():
    """Get the full claim checklist"""
    return CLAIM_CHECKLIST


# Required documents for insurance claim
REQUIRED_DOCUMENTS = [
    {'name': 'Constat Amiable (Accident Report Form)', 'required': True, 'description': 'Signed by both parties'},
    {'name': 'Police Report (Procès-verbal)', 'required': True, 'description': 'From local police station'},
    {'name': 'Driver\'s License', 'required': True, 'description': 'Copy of valid license'},
    {'name': 'Vehicle Registration (Carte Grise)', 'required': True, 'description': 'Copy of registration document'},
    {'name': 'Insurance Policy', 'required': True, 'description': 'Your current insurance certificate'},
    {'name': 'Photos of Damage', 'required': True, 'description': 'Multiple angles of all damage'},
    {'name': 'Photos of Scene', 'required': False, 'description': 'Road conditions, signs, positions'},
    {'name': 'Witness Statements', 'required': False, 'description': 'Written statements with contact info'},
    {'name': 'Medical Reports', 'required': False, 'description': 'Required if injuries occurred'},
    {'name': 'Repair Estimates', 'required': True, 'description': 'From approved repair shops'},
]


def get_required_documents():
    """Get list of required documents for claim"""
    return REQUIRED_DOCUMENTS
