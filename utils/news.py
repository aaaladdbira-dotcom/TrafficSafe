"""
Traffic News Service for Tunisia
================================
Fetch real-time traffic news from reliable Tunisian sources
Including national news agencies, radio stations, and newspapers
"""

import requests
import feedparser
from datetime import datetime, timedelta
import re
import hashlib
import json
from typing import List, Dict, Optional
import warnings
import urllib3

# Suppress SSL warnings for problematic Tunisian news sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# ============== REAL TUNISIAN NEWS SOURCES ==============
# These are actual working RSS feeds from Tunisian media

NEWS_SOURCES = [
    # National News Agency
    {
        'name': 'TAP - Tunis Afrique Presse',
        'rss_url': 'https://www.tap.info.tn/fr/rss/portal-Accueil',
        'website': 'https://www.tap.info.tn',
        'language': 'fr',
        'type': 'agency',
        'reliable': True
    },
    # Radio Stations
    {
        'name': 'Mosaïque FM',
        'rss_url': 'https://www.mosaiquefm.net/fr/rss/actualite-tunisie',
        'website': 'https://www.mosaiquefm.net',
        'language': 'fr',
        'type': 'radio',
        'reliable': True
    },
    {
        'name': 'Jawhara FM',
        'rss_url': 'https://www.jawharafm.net/fr/rss',
        'website': 'https://www.jawharafm.net',
        'language': 'fr',
        'type': 'radio',
        'reliable': True
    },
    # Newspapers and News Sites
    {
        'name': 'Business News Tunisia',
        'rss_url': 'https://www.businessnews.com.tn/rss.xml',
        'website': 'https://www.businessnews.com.tn',
        'language': 'fr',
        'type': 'newspaper',
        'reliable': True
    },
    {
        'name': 'Tunisie Numérique',
        'rss_url': 'https://www.tunisienumerique.com/feed/',
        'website': 'https://www.tunisienumerique.com',
        'language': 'fr',
        'type': 'news',
        'reliable': True
    },
    {
        'name': 'Kapitalis',
        'rss_url': 'https://kapitalis.com/tunisie/feed/',
        'website': 'https://kapitalis.com',
        'language': 'fr',
        'type': 'news',
        'reliable': True
    },
    {
        'name': 'Webdo Tunisia',
        'rss_url': 'https://www.webdo.tn/feed/',
        'website': 'https://www.webdo.tn',
        'language': 'fr',
        'type': 'news',
        'reliable': True
    },
    {
        'name': 'Leaders Tunisia',
        'rss_url': 'https://www.leaders.com.tn/feed/',
        'website': 'https://www.leaders.com.tn',
        'language': 'fr',
        'type': 'newspaper',
        'reliable': True
    },
    {
        'name': 'Gnetnews',
        'rss_url': 'https://www.gnetnews.com/feed/',
        'website': 'https://www.gnetnews.com',
        'language': 'fr',
        'type': 'news',
        'reliable': True
    },
    {
        'name': 'African Manager',
        'rss_url': 'https://africanmanager.com/feed/',
        'website': 'https://africanmanager.com',
        'language': 'fr',
        'type': 'news',
        'reliable': True
    }
]

# Keywords to identify traffic/transport/accident news
# More specific keywords to avoid false positives like drug trafficking
TRAFFIC_KEYWORDS = {
    'fr': [
        # Core road/accident terms
        'accident de la route', 'accident de circulation', 'accident mortel', 'accident de voiture',
        'collision', 'carambolage', 'renversement', 'dérapage',
        # Road infrastructure
        'autoroute', 'route nationale', 'gp1', 'gp2', 'rocade', 'périphérique', 'tunnel',
        'chaussée', 'voie rapide', 'bretelle',
        # Traffic/circulation - need context
        'embouteillage', 'bouchon', 'ralentissement', 'fluidité',
        # Vehicles - specific contexts
        'véhicule', 'voiture', 'camion', 'poids lourd', 'moto', 'motocycliste',
        'bus', 'autocar', 'taxi', 'louage',
        # People involved
        'conducteur', 'chauffeur', 'piéton', 'passager', 'automobiliste', 'motard',
        # Injuries/casualties (road context)
        'blessé grave', 'hospitalisé', 'victime de la route',
        # Emergency services
        'protection civile', 'ambulance', 'samu', 'secours routier', 'dépannage',
        'garde nationale',
        # Road events
        'travaux routiers', 'déviation', 'fermeture de route', 'coupure de route',
        'contrôle routier', 'radar', 'excès de vitesse', 'infraction routière',
        # Weather affecting roads
        'verglas', 'chaussée glissante', 'visibilité réduite', 'conditions météo',
        # Tunisian road names
        'autoroute a1', 'autoroute a3', 'autoroute a4'
    ],
    'en': [
        'road accident', 'car accident', 'traffic accident', 'car crash', 'collision',
        'highway', 'freeway', 'motorway', 'road closure',
        'vehicle', 'car', 'truck', 'motorcycle', 'bus',
        'driver', 'pedestrian', 'motorist',
        'injured', 'hospitalized', 'road victim',
        'roadwork', 'detour', 'road construction',
        'speed limit', 'traffic violation', 'checkpoint'
    ],
    'ar': [
        'حادث مرور', 'حادث طريق', 'حادث سير', 'تصادم', 'انقلاب',
        'طريق سيار', 'طريق وطني', 'شارع',
        'سيارة', 'شاحنة', 'حافلة', 'دراجة نارية',
        'سائق', 'راجل', 'مشاة',
        'جرحى', 'وفاة', 'ضحايا الطريق',
        'أشغال طرقية', 'انحراف', 'إغلاق طريق',
        'رادار', 'مخالفة', 'سرعة'
    ]
}

# Exclusion keywords - if these are in the title, it's probably NOT traffic news
EXCLUSION_KEYWORDS = [
    'trafic de drogue', 'trafic de cocaïne', 'trafic humain', 'trafic d\'organes',
    'trafic de migrants', 'trafic de devises', 'trafic d\'armes',
    'drug trafficking', 'human trafficking', 'arms trafficking',
    'réseau de trafic', 'filière', 'contrebande', 'dealers'
]

# Cache for news data
_news_cache = {
    'data': [],
    'timestamp': None,
    'ttl': 300  # 5 minutes
}

_alerts_cache = {
    'data': [],
    'timestamp': None,
    'ttl': 180  # 3 minutes
}


class NewsService:
    """Service for fetching real-time traffic news from Tunisia"""
    
    @staticmethod
    def fetch_rss_feed(url: str, timeout: int = 15) -> Optional[feedparser.FeedParserDict]:
        """Fetch and parse an RSS feed with proper error handling"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8,ar;q=0.7'
            }
            # Disable SSL verification for some problematic Tunisian sites
            response = requests.get(url, timeout=timeout, headers=headers, verify=False)
            
            if response.ok:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    return feed
        except requests.Timeout:
            print(f"Timeout fetching RSS: {url}")
        except requests.RequestException as e:
            print(f"Error fetching RSS {url}: {e}")
        except Exception as e:
            print(f"Unexpected error parsing RSS {url}: {e}")
        return None
    
    @staticmethod
    def is_traffic_related(text: str, language: str = 'fr') -> bool:
        """Check if text contains traffic-related keywords (road/vehicle traffic, not drug trafficking)"""
        if not text:
            return False
        text_lower = text.lower()
        
        # First check exclusion keywords - if these are present, it's NOT traffic news
        for excl in EXCLUSION_KEYWORDS:
            if excl in text_lower:
                return False
        
        keywords = TRAFFIC_KEYWORDS.get(language, TRAFFIC_KEYWORDS['fr'])
        
        # Count matching keywords - require at least 1 match
        matches = sum(1 for kw in keywords if kw in text_lower)
        return matches >= 1
    
    @staticmethod
    def parse_date(date_input) -> datetime:
        """Parse various date formats to datetime"""
        if isinstance(date_input, datetime):
            return date_input
        
        if hasattr(date_input, 'tm_year'):  # struct_time
            try:
                return datetime(*date_input[:6])
            except:
                pass
        
        if not date_input or not isinstance(date_input, str):
            return datetime.now()
        
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S GMT',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d %b %Y %H:%M',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_input.strip(), fmt)
            except:
                continue
        
        return datetime.now()
    
    @staticmethod
    def clean_html(text: str) -> str:
        """Remove HTML tags and clean text"""
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean)
        # Remove special characters
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&#8217;', "'")
        clean = clean.replace('&#8230;', '...')
        return clean.strip()[:500]
    
    @staticmethod
    def generate_id(title: str, source: str) -> str:
        """Generate unique ID for news item"""
        content = f"{title}{source}{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    @staticmethod
    def extract_location(text: str) -> Optional[str]:
        """Extract location from news text"""
        # Tunisian governorates and cities
        locations = [
            'Tunis', 'Ariana', 'Ben Arous', 'Manouba', 'Nabeul', 'Zaghouan',
            'Bizerte', 'Béja', 'Jendouba', 'Le Kef', 'Siliana', 'Sousse',
            'Monastir', 'Mahdia', 'Sfax', 'Kairouan', 'Kasserine', 'Sidi Bouzid',
            'Gabès', 'Médenine', 'Tataouine', 'Gafsa', 'Tozeur', 'Kébili',
            'Hammamet', 'Djerba', 'Tabarka', 'Ras Jedir'
        ]
        
        text_lower = text.lower()
        for loc in locations:
            if loc.lower() in text_lower:
                return loc
        return None
    
    @staticmethod
    def categorize_news(text: str) -> str:
        """Categorize news type based on content"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ['accident', 'collision', 'crash', 'mort', 'décès', 'victime', 'blessé']):
            return 'accident'
        if any(w in text_lower for w in ['travaux', 'construction', 'roadwork', 'chantier']):
            return 'roadwork'
        if any(w in text_lower for w in ['météo', 'pluie', 'inondation', 'weather', 'flood', 'orage']):
            return 'weather'
        if any(w in text_lower for w in ['fermeture', 'closure', 'coupure', 'déviation']):
            return 'closure'
        if any(w in text_lower for w in ['contrôle', 'police', 'radar', 'amende']):
            return 'police'
        if any(w in text_lower for w in ['transport', 'bus', 'métro', 'train']):
            return 'transport'
        return 'traffic'
    
    @staticmethod
    def get_severity(text: str) -> str:
        """Determine severity level from news content"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ['mort', 'décès', 'fatal', 'death', 'tué', 'killed', 'grave']):
            return 'critical'
        if any(w in text_lower for w in ['blessé', 'injured', 'collision', 'accident grave', 'hospitalisé']):
            return 'high'
        if any(w in text_lower for w in ['accident', 'embouteillage', 'perturbation', 'traffic jam']):
            return 'medium'
        return 'low'
    
    @classmethod
    def get_all_news(cls, max_items: int = 50, traffic_only: bool = False) -> List[Dict]:
        """
        Fetch all news from all sources
        
        Args:
            max_items: Maximum number of items to return
            traffic_only: If True, only return traffic-related news
        """
        global _news_cache
        
        # Check cache
        if _news_cache['timestamp'] and _news_cache['data']:
            age = (datetime.now() - _news_cache['timestamp']).total_seconds()
            if age < _news_cache['ttl']:
                data = _news_cache['data']
                if traffic_only:
                    data = [n for n in data if n.get('is_traffic_related', False)]
                return data[:max_items]
        
        all_news = []
        
        for source in NEWS_SOURCES:
            try:
                feed = cls.fetch_rss_feed(source['rss_url'])
                if not feed or not feed.entries:
                    continue
                
                for entry in feed.entries[:15]:  # Max 15 per source
                    title = entry.get('title', '')
                    summary = cls.clean_html(entry.get('summary', entry.get('description', '')))
                    link = entry.get('link', '')
                    
                    if not title:
                        continue
                    
                    # Parse publication date
                    pub_date = entry.get('published_parsed') or entry.get('updated_parsed')
                    if pub_date:
                        try:
                            published = datetime(*pub_date[:6])
                        except:
                            published = datetime.now()
                    else:
                        published = cls.parse_date(entry.get('published', entry.get('updated', '')))
                    
                    # Check if traffic related
                    combined_text = f"{title} {summary}"
                    is_traffic = cls.is_traffic_related(combined_text, source['language'])
                    
                    news_item = {
                        'id': cls.generate_id(title, source['name']),
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'source': source['name'],
                        'source_type': source['type'],
                        'website': source['website'],
                        'language': source['language'],
                        'published': published,
                        'category': cls.categorize_news(combined_text),
                        'severity': cls.get_severity(combined_text),
                        'location': cls.extract_location(combined_text),
                        'is_traffic_related': is_traffic
                    }
                    all_news.append(news_item)
                    
            except Exception as e:
                print(f"Error processing source {source['name']}: {e}")
                continue
        
        # Sort by date (newest first)
        all_news.sort(key=lambda x: x['published'], reverse=True)
        
        # Update cache
        _news_cache['data'] = all_news
        _news_cache['timestamp'] = datetime.now()
        
        if traffic_only:
            all_news = [n for n in all_news if n.get('is_traffic_related', False)]
        
        return all_news[:max_items]
    
    @classmethod
    def get_traffic_news(cls, max_items: int = 30) -> List[Dict]:
        """Get only traffic-related news"""
        return cls.get_all_news(max_items=max_items, traffic_only=True)
    
    @classmethod
    def get_news_feed(cls, max_items: int = 20) -> List[Dict]:
        """Get general news feed (for the Traffic News page)"""
        return cls.get_all_news(max_items=max_items, traffic_only=False)
    
    @staticmethod
    def clear_cache():
        """Clear all caches"""
        global _news_cache, _alerts_cache
        _news_cache = {'data': [], 'timestamp': None, 'ttl': 300}
        _alerts_cache = {'data': [], 'timestamp': None, 'ttl': 180}


# ============== TRAFFIC ALERTS ==============
# These are generated from recent accident news + simulated real-time alerts

def generate_alerts_from_news() -> List[Dict]:
    """Generate traffic alerts from recent news"""
    alerts = []
    
    try:
        news = NewsService.get_all_news(max_items=30, traffic_only=True)
        
        for item in news:
            # Only create alerts for recent and relevant news
            age_hours = (datetime.now() - item['published']).total_seconds() / 3600
            if age_hours > 24:  # Only last 24 hours
                continue
            
            if item['severity'] in ['critical', 'high', 'medium']:
                alert = {
                    'id': f"news_{item['id']}",
                    'type': item['category'],
                    'severity': item['severity'],
                    'title': item['title'][:100],
                    'description': item['summary'][:200] if item['summary'] else item['title'],
                    'location': item['location'] or 'Tunisia',
                    'governorate': item['location'] or 'National',
                    'timestamp': item['published'],
                    'source': item['source'],
                    'link': item['link'],
                    'status': 'active'
                }
                alerts.append(alert)
    except Exception as e:
        print(f"Error generating alerts from news: {e}")
    
    return alerts


def get_simulated_alerts() -> List[Dict]:
    """Get simulated real-time alerts (for demo purposes when news is unavailable)"""
    now = datetime.now()
    
    return [
        {
            'id': 'live_001',
            'type': 'traffic',
            'severity': 'medium',
            'title': 'Embouteillage sur l\'autoroute A1 - Direction Sousse',
            'description': 'Ralentissement important entre la sortie Hammamet Sud et Enfidha. Temps de parcours augmenté de 20 minutes.',
            'location': 'Autoroute A1, Km 40-55',
            'governorate': 'Nabeul',
            'timestamp': now - timedelta(minutes=15),
            'source': 'TrafficSafe Live',
            'status': 'active'
        },
        {
            'id': 'live_002',
            'type': 'roadwork',
            'severity': 'low',
            'title': 'Travaux de réfection - Avenue Habib Bourguiba',
            'description': 'Travaux de nuit entre 22h et 5h. Circulation alternée. Prévoir des délais.',
            'location': 'Avenue Habib Bourguiba, Tunis Centre',
            'governorate': 'Tunis',
            'timestamp': now - timedelta(hours=2),
            'source': 'Municipalité de Tunis',
            'status': 'active'
        },
        {
            'id': 'live_003',
            'type': 'weather',
            'severity': 'high',
            'title': 'Alerte météo - Fortes pluies attendues',
            'description': 'L\'INM prévoit de fortes pluies sur le nord et le centre. Risque d\'inondation sur les routes. Prudence recommandée.',
            'location': 'Nord et Centre de la Tunisie',
            'governorate': 'National',
            'timestamp': now - timedelta(minutes=45),
            'source': 'INM Tunisie',
            'status': 'active'
        },
        {
            'id': 'live_004',
            'type': 'police',
            'severity': 'low',
            'title': 'Contrôle routier - GP1 Sfax',
            'description': 'Point de contrôle de la Garde Nationale sur la GP1 à l\'entrée de Sfax. Vérification des documents.',
            'location': 'GP1, Entrée Nord Sfax',
            'governorate': 'Sfax',
            'timestamp': now - timedelta(hours=1),
            'source': 'Garde Nationale',
            'status': 'active'
        }
    ]


def get_traffic_alerts(governorate: Optional[str] = None) -> List[Dict]:
    """
    Get current traffic alerts combining news-based and simulated alerts
    
    Args:
        governorate: Filter by governorate name
    """
    global _alerts_cache
    
    # Check cache
    if _alerts_cache['timestamp'] and _alerts_cache['data']:
        age = (datetime.now() - _alerts_cache['timestamp']).total_seconds()
        if age < _alerts_cache['ttl']:
            alerts = _alerts_cache['data']
            if governorate:
                alerts = [a for a in alerts if governorate.lower() in a.get('governorate', '').lower()]
            return alerts
    
    # Generate alerts from news
    news_alerts = generate_alerts_from_news()
    
    # Add simulated alerts if not enough news alerts
    if len(news_alerts) < 4:
        news_alerts.extend(get_simulated_alerts())
    
    # Remove duplicates based on similar titles
    seen_titles = set()
    unique_alerts = []
    for alert in news_alerts:
        title_key = alert['title'][:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_alerts.append(alert)
    
    # Sort by timestamp
    unique_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Update cache
    _alerts_cache['data'] = unique_alerts
    _alerts_cache['timestamp'] = datetime.now()
    
    if governorate:
        unique_alerts = [a for a in unique_alerts if governorate.lower() in a.get('governorate', '').lower()]
    
    return unique_alerts


def get_alert_by_id(alert_id: str) -> Optional[Dict]:
    """Get specific alert by ID"""
    alerts = get_traffic_alerts()
    for alert in alerts:
        if alert['id'] == alert_id:
            return alert
    return None
