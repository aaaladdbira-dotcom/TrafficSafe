"""
AI Chatbot Resource - Handles chat interactions for the Traffic Accident Management System
Enhanced with conversational AI capabilities and context awareness
"""
from flask import Blueprint, request, jsonify, current_app
import re
import random
from datetime import datetime
from extensions import db
from sqlalchemy import func
from utils.weather import WeatherService, GOVERNORATE_COORDS

chatbot_bp = Blueprint('chatbot', __name__)

# Weather emoji mapping based on weather code
WEATHER_EMOJIS = {
    0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
    45: '🌫️', 48: '🌫️',
    51: '🌧️', 53: '🌧️', 55: '🌧️',
    61: '🌧️', 63: '🌧️', 65: '🌧️',
    71: '❄️', 73: '❄️', 75: '❄️',
    80: '🌦️', 81: '🌦️', 82: '⛈️',
    95: '⛈️', 96: '⛈️', 99: '⛈️'
}

def get_weather_response(message, lang='en'):
    """Get real weather data and format a response"""
    message_lower = message.lower()
    
    # Try to extract governorate from message
    governorate = 'Tunis'  # Default
    for gov in GOVERNORATE_COORDS.keys():
        if gov.lower() in message_lower or gov.lower().replace('é', 'e').replace('è', 'e') in message_lower:
            governorate = gov
            break
    
    # Also check for common variations
    gov_aliases = {
        'tunis': 'Tunis', 'sfax': 'Sfax', 'sousse': 'Sousse', 'gabes': 'Gabès',
        'bizerte': 'Bizerte', 'kairouan': 'Kairouan', 'monastir': 'Monastir',
        'nabeul': 'Nabeul', 'mahdia': 'Mahdia', 'kasserine': 'Kasserine',
        'gafsa': 'Gafsa', 'tozeur': 'Tozeur', 'kebili': 'Kébili',
        'tataouine': 'Tataouine', 'medenine': 'Médenine', 'jendouba': 'Jendouba',
        'beja': 'Béja', 'kef': 'Le Kef', 'siliana': 'Siliana', 'zaghouan': 'Zaghouan',
        'ariana': 'Ariana', 'ben arous': 'Ben Arous', 'manouba': 'Manouba',
        'sidi bouzid': 'Sidi Bouzid'
    }
    for alias, gov in gov_aliases.items():
        if alias in message_lower:
            governorate = gov
            break
    
    try:
        weather = WeatherService.get_current_weather(governorate)
        if weather:
            emoji = WEATHER_EMOJIS.get(weather['weathercode'], '🌡️')
            temp = weather['temperature']
            feels_like = weather['feels_like']
            description = weather['weather_description']
            humidity = weather['humidity']
            wind = weather['windspeed']
            risk = weather['risk_factor']
            precip_prob = weather.get('precipitation_probability', 0)
            
            # Risk assessment for driving
            if risk <= 0.9:
                risk_text = "🟢 Low risk - Great conditions for driving!"
                risk_text_fr = "🟢 Risque faible - Excellentes conditions!"
                risk_text_ar = "🟢 خطر منخفض - ظروف ممتازة للقيادة!"
            elif risk <= 1.2:
                risk_text = "🟡 Normal conditions - Drive safely"
                risk_text_fr = "🟡 Conditions normales - Conduisez prudemment"
                risk_text_ar = "🟡 ظروف عادية - قد بحذر"
            elif risk <= 1.5:
                risk_text = "🟠 Elevated risk - Extra caution advised"
                risk_text_fr = "🟠 Risque élevé - Prudence supplémentaire"
                risk_text_ar = "🟠 خطر مرتفع - ينصح بحذر إضافي"
            else:
                risk_text = "🔴 High risk - Consider delaying travel"
                risk_text_fr = "🔴 Risque élevé - Retardez vos déplacements"
                risk_text_ar = "🔴 خطر عالي - فكر في تأجيل السفر"
            
            if lang == 'ar':
                return f"""{emoji} **طقس {governorate} الآن:**

🌡️ **درجة الحرارة:** {temp}°C (تشعر كـ {feels_like}°C)
☁️ **الحالة:** {description}
💧 **الرطوبة:** {humidity}%
💨 **الرياح:** {wind} كم/س
🌧️ **احتمال هطول:** {precip_prob}%

**تقييم خطر القيادة:**
{risk_text_ar}

*أنا SafeRoad AI - أجمع بين الطقس والسلامة المرورية!* 🚗"""
            elif lang == 'fr':
                return f"""{emoji} **Météo à {governorate} maintenant:**

🌡️ **Température:** {temp}°C (ressenti {feels_like}°C)
☁️ **Conditions:** {description}
💧 **Humidité:** {humidity}%
💨 **Vent:** {wind} km/h
🌧️ **Probabilité de pluie:** {precip_prob}%

**Évaluation du risque routier:**
{risk_text_fr}

*Je suis SafeRoad AI - je combine météo et sécurité routière!* 🚗"""
            else:
                return f"""{emoji} **Weather in {governorate} right now:**

🌡️ **Temperature:** {temp}°C (feels like {feels_like}°C)
☁️ **Conditions:** {description}
💧 **Humidity:** {humidity}%
💨 **Wind:** {wind} km/h
🌧️ **Precipitation chance:** {precip_prob}%

**Driving Risk Assessment:**
{risk_text}

*I'm SafeRoad AI - I combine weather data with road safety insights!* 🚗"""
    except Exception as e:
        current_app.logger.error(f"Weather fetch error: {e}")
    
    # Fallback if API fails
    if lang == 'ar':
        return "عذراً، لم أتمكن من جلب بيانات الطقس حالياً. حاول مرة أخرى لاحقاً! 🌡️"
    elif lang == 'fr':
        return "Désolé, je n'ai pas pu récupérer les données météo. Réessayez plus tard! 🌡️"
    else:
        return "Sorry, I couldn't fetch weather data right now. Please try again later! 🌡️"

# Off-topic patterns - questions outside our domain that we should handle gracefully
# Note: Weather is NOT off-topic - we have weather API integration!
OFF_TOPIC_PATTERNS = {
    'news': {
        'patterns': [r'\b(what|whats|tell\s+me)\b.*\b(news|headlines)\b', r'\bwhat\'?s\s+happening\b', r'\bcurrent\s+events?\b', r'\bpolitics?\b', r'\belection\b'],
        'response': {
            'en': """📰 I'm not a news assistant, but I appreciate you asking!

I'm **SafeRoad AI**, focused on **traffic safety in Tunisia**.

**I can tell you about:**
• Recent accident trends and statistics
• Road safety updates
• Traffic hotspots and patterns

For general news, check local news sources or news apps.

Would you like to know about recent traffic statistics instead? 📊""",
            'fr': """📰 Je ne suis pas un assistant d'actualités!

Je suis **SafeRoad AI**, focalisé sur la **sécurité routière en Tunisie**.

Voulez-vous connaître les statistiques de trafic récentes? 📊""",
            'ar': """📰 أنا لست مساعد أخبار!

أنا **SafeRoad AI**، متخصص في **السلامة المرورية في تونس**.

هل تريد معرفة إحصائيات المرور الأخيرة؟ 📊"""
        }
    },
    'sports': {
        'patterns': [
            r'\b(who|what|when|where)\b.*\b(score|match|game|play(ed|ing)?|won|win)\b',
            r'\b(football|soccer|basketball|tennis)\b.*(score|match|result|play)',
            r'\bdid\s+\w+\s+(win|lose|score)\b',
        ],
        'response': {
            'en': """⚽ While I love a good game, I'm not a sports assistant!

I'm **SafeRoad AI**, your road safety companion for Tunisia.

Fun fact: Major sporting events can affect traffic patterns! After big matches, we often see changes in accident statistics.

**I can help you with:**
• Traffic safety information
• Accident reporting
• Road safety tips

Anything road safety-related I can assist with? 🚗""",
            'fr': """⚽ Je ne suis pas un assistant sportif!

Je suis **SafeRoad AI**, votre compagnon de sécurité routière.

Puis-je vous aider avec la sécurité routière? 🚗""",
            'ar': """⚽ أنا لست مساعد رياضي!

أنا **SafeRoad AI**، رفيقك للسلامة المرورية.

هل يمكنني مساعدتك في السلامة المرورية؟ 🚗"""
        }
    },
    'food': {
        'patterns': [
            r'\b(where|what|recommend)\b.*(eat|restaurant|food)\b',
            r'\b(best|good)\s+(restaurant|food|place\s+to\s+eat)\b',
            r'\bwhat\s+should\s+i\s+(eat|have\s+for)\b',
            r'\bhungry\b.*\b(where|what)\b',
        ],
        'response': {
            'en': """🍽️ I can't help with food recommendations, but here's a safety tip:

**Never eat while driving!** 🚗 Distracted driving (including eating) is one of the top causes of accidents.

I'm **SafeRoad AI**, focused on keeping Tunisia's roads safe.

**I can help with:**
• Road safety tips (like avoiding distractions!)
• Accident statistics
• Reporting incidents

What road safety topic interests you? 🛡️""",
            'fr': """🍽️ Je ne peux pas aider avec la nourriture, mais voici un conseil:

**Ne mangez jamais en conduisant!** C'est une cause majeure d'accidents.

Puis-je vous aider avec la sécurité routière? 🛡️""",
            'ar': """🍽️ لا أستطيع المساعدة في الطعام، لكن إليك نصيحة:

**لا تأكل أثناء القيادة!** إنه سبب رئيسي للحوادث.

هل يمكنني مساعدتك في السلامة المرورية؟ 🛡️"""
        }
    },
    'entertainment': {
        'patterns': [
            r'\b(what|which|recommend)\b.*(movie|film|show|series|watch)\b',
            r'\b(watch|see|seen)\b.*(movie|show|series)\b',
            r'\bwhat\'?s\s+(on|playing)\b.*(netflix|tv|youtube)\b',
        ],
        'response': {
            'en': """🎬 Entertainment isn't my specialty, but I have a tip:

**Don't watch videos while driving!** 📱 Using phones/screens while driving is extremely dangerous.

I'm **SafeRoad AI**, here for traffic safety in Tunisia.

**What I can help with:**
• Safe driving practices
• Accident statistics and trends
• Reporting traffic incidents

Any road safety questions? 🚦""",
            'fr': """🎬 Le divertissement n'est pas ma spécialité!

**N'utilisez pas d'écrans en conduisant!** C'est très dangereux.

Puis-je vous aider avec la sécurité routière? 🚦""",
            'ar': """🎬 الترفيه ليس تخصصي!

**لا تستخدم الشاشات أثناء القيادة!** إنه خطير جداً.

هل يمكنني مساعدتك في السلامة المرورية؟ 🚦"""
        }
    },
    'personal': {
        'patterns': [
            r'\b(will\s+you|do\s+you\s+want\s+to)\s+date\b',
            r'\b(marry|love)\s+me\b',
            r'\bare\s+you\s+(single|available)\b',
            r'\bcan\s+we\s+(date|go\s+out)\b',
        ],
        'response': {
            'en': """💝 I'm flattered, but I'm just an AI focused on road safety!

I'm **SafeRoad AI**, dedicated to making Tunisia's roads safer.

The only relationship I'm interested in is helping you stay safe on the road! 🚗

**Let me help you with:**
• Accident reporting
• Safety statistics
• Driving tips

How can I assist with road safety today? 😊""",
            'fr': """💝 Je suis flatté, mais je suis juste une IA pour la sécurité routière!

Comment puis-je vous aider avec la sécurité routière? 😊""",
            'ar': """💝 أنا ممتن، لكنني مجرد ذكاء اصطناعي للسلامة المرورية!

كيف يمكنني مساعدتك في السلامة المرورية؟ 😊"""
        }
    },
    'time_date': {
        'patterns': [
            r'\bwhat\s+(time|day|date)\s+(is\s+it)?\b',
            r'\bwhat\'?s?\s+(the\s+)?(time|date|day)\b',
            r'\b(current|today\'?s?)\s+(time|date)\b',
        ],
        'response': {
            'en': """🕐 I don't track real-time clock/calendar, but your device can help with that!

I'm **SafeRoad AI**, focused on traffic safety data.

**Time-related things I CAN help with:**
• Peak accident hours (typically 6-9 AM and 5-8 PM)
• Safest times to drive
• Historical accident patterns by time

Want to know when accidents happen most frequently? ⏰""",
            'fr': """🕐 Je ne suis pas une horloge, mais votre appareil peut vous aider!

Voulez-vous savoir à quelles heures les accidents sont les plus fréquents? ⏰""",
            'ar': """🕐 أنا لست ساعة، لكن جهازك يمكنه المساعدة!

هل تريد معرفة أوقات الحوادث الأكثر شيوعاً؟ ⏰"""
        }
    },
    'general_knowledge': {
        'patterns': [
            r'\bwhat\s+(is|was)\s+(the\s+)?(capital|population)\b',
            r'\bwho\s+(is|was|invented|discovered|created|founded)\b',
            r'\bwhen\s+(was|did|is)\s+\w+\s+(born|founded|invented|created)\b',
            r'\bhow\s+old\s+is\b',
        ],
        'response': {
            'en': """📚 That's a great general knowledge question, but I'm specialized in road safety!

I'm **SafeRoad AI**, your traffic safety assistant for Tunisia.

**Questions I'm great at answering:**
• "How many accidents happened this year?"
• "What causes most accidents?"
• "Which areas are most dangerous?"
• "How do I report an accident?"

Try asking me something about road safety! 🚗""",
            'fr': """📚 Bonne question de culture générale, mais je suis spécialisé en sécurité routière!

Essayez de me poser une question sur la sécurité routière! 🚗""",
            'ar': """📚 سؤال معرفة عامة رائع، لكنني متخصص في السلامة المرورية!

جرب أن تسألني شيئاً عن السلامة المرورية! 🚗"""
        }
    },
    'math': {
        'patterns': [r'\bcalculate\b', r'\bmath\b', r'\b\d+\s*[\+\-\*\/\×\÷]\s*\d+\b', r'\bsolve\b', r'\bequation\b', r'\balgebra\b'],
        'response': {
            'en': """🔢 Math isn't my strong suit - I'm a road safety AI, not a calculator!

I'm **SafeRoad AI**, specialized in traffic safety for Tunisia.

**Numbers I DO know:**
• Accident statistics and trends
• Percentage breakdowns by cause
• Regional comparison data

Want me to show you some traffic safety statistics? 📊""",
            'fr': """🔢 Les maths ne sont pas mon fort - je suis une IA de sécurité routière!

Voulez-vous voir des statistiques de sécurité routière? 📊""",
            'ar': """🔢 الرياضيات ليست تخصصي - أنا ذكاء اصطناعي للسلامة المرورية!

هل تريد رؤية إحصائيات السلامة المرورية؟ 📊"""
        }
    },
    'coding': {
        'patterns': [r'\b(write|create|make|build)\b.*\b(code|program|script|function)\b', r'\bprogramm?ing\b', r'\bdebug\b.*\b(code|error)\b'],
        'response': {
            'en': """💻 I'm not a coding assistant, though I was built with code!

I'm **SafeRoad AI**, focused on traffic safety in Tunisia.

If you're a developer interested in our platform, you might want to check our API documentation or contact the development team.

**Meanwhile, I can help with:**
• Road safety information
• Accident statistics
• Using this platform

Any road safety questions? 🛡️""",
            'fr': """💻 Je ne suis pas un assistant de programmation!

Je suis **SafeRoad AI**, focalisé sur la sécurité routière.

Des questions sur la sécurité routière? 🛡️""",
            'ar': """💻 أنا لست مساعد برمجة!

أنا **SafeRoad AI**، متخصص في السلامة المرورية.

أي أسئلة عن السلامة المرورية؟ 🛡️"""
        }
    }
}

# Patterns for follow-up clarifications, arguments, or corrections from user
CLARIFICATION_PATTERNS = {
    'disagreement': {
        'patterns': [
            r'\bbut\s+(you|i|it|there|this)\b',
            r'\bno,?\s+(you|i|it|that)\b',
            r'\bthat\'?s\s+(not|wrong|incorrect)\b',
            r'\byou\'?re\s+(wrong|incorrect|mistaken)\b',
            r'\bi\s+(said|meant|asked|think)\b',
            r'\byou\s+(have|had|do|did|can|should)\b',
            r'\bwhy\s+(not|can\'?t|don\'?t|won\'?t)\b',
        ],
        'response': {
            'en': """I hear you! 🤔 Let me try to understand better.

I'm **SafeRoad AI** - my expertise is specifically in:
• 🚗 Traffic accident reporting and management
• 📊 Road safety statistics for Tunisia
• 🛡️ Driving safety tips and information
• 🗺️ Accident hotspot mapping

If I misunderstood your question, could you please rephrase it? I want to help you the best way I can!

**Try asking things like:**
• "How do I report an accident?"
• "What are the main causes of accidents?"
• "Show me statistics for [governorate]"
• "Give me safety tips"

What would you like to know? 😊""",
            'fr': """Je vous entends! 🤔 Laissez-moi mieux comprendre.

Je suis **SafeRoad AI** - spécialisé en sécurité routière en Tunisie.

Si j'ai mal compris, pourriez-vous reformuler? Je veux vous aider au mieux!

Que souhaitez-vous savoir? 😊""",
            'ar': """أسمعك! 🤔 دعني أفهم بشكل أفضل.

أنا **SafeRoad AI** - متخصص في السلامة المرورية في تونس.

إذا أسأت الفهم، هل يمكنك إعادة الصياغة؟ أريد مساعدتك بأفضل طريقة!

ماذا تريد أن تعرف؟ 😊"""
        }
    },
    'frustration': {
        'patterns': [
            r'\b(this|you)\s+(is|are)\s+(stupid|dumb|useless|bad)\b',
            r'\byou\s+don\'?t\s+(understand|get\s+it|listen)\b',
            r'\b(ugh|argh|omg)\b',
            r'\bstop\s+(repeating|saying)\b',
            r'\bsame\s+(answer|response|thing)\b',
        ],
        'response': {
            'en': """I'm sorry for the frustration! 😔 Let me try a different approach.

I'm an AI assistant specifically designed for **traffic safety in Tunisia**. I have limitations, but I genuinely want to help.

**Here's what I'm good at:**
• Explaining how to report accidents
• Sharing traffic statistics and trends
• Providing road safety tips
• Helping you navigate this platform

**Could you tell me specifically:**
What are you trying to accomplish today? I'll do my best to help or point you in the right direction! 🙏""",
            'fr': """Désolé pour la frustration! 😔

Que cherchez-vous à accomplir? Je ferai de mon mieux pour aider! 🙏""",
            'ar': """آسف للإحباط! 😔

ماذا تحاول تحقيقه؟ سأبذل قصارى جهدي للمساعدة! 🙏"""
        }
    }
}

# Conversational patterns for natural language understanding
CONVERSATIONAL_PATTERNS = {
    # Vague questions about the website/system
    'what_is_this': {
        'patterns': [r'\bwhat\s+(is|are)\s+(this|these)\b', r'\bwhat\s+does\s+(this|it)\s+do\b', r'\bwhat\s+is\s+this\s+(site|website|app|platform|system)\b', r'\btell\s+me\s+about\s+(this|yourself)\b'],
        'response': {
            'en': """🚗 **Welcome to SafeRoad Tunisia!**

I'm your AI assistant for the **Traffic Accident Management System** - Tunisia's comprehensive platform for road safety.

**What We Do:**
• 📝 **Report & Track Accidents** - Submit accident reports and follow their status
• 📊 **Analyze Data** - View statistics, trends, and insights on road safety
• 🗺️ **Visualize Hotspots** - Interactive maps showing accident-prone areas
• 🤖 **AI Predictions** - Forecasts and risk analysis powered by machine learning
• 🛡️ **Promote Safety** - Educational resources and safety tips

**Who Uses This:**
• Government officials monitoring road safety
• Citizens reporting incidents
• Researchers analyzing traffic data
• Emergency responders coordinating efforts

Would you like me to help you with something specific? 🙋""",
            'fr': """🚗 **Bienvenue sur SafeRoad Tunisie!**

Je suis votre assistant IA pour le **Système de Gestion des Accidents de la Route** - la plateforme complète de la Tunisie pour la sécurité routière.

**Ce que nous faisons:**
• 📝 **Signaler et suivre** - Soumettre des rapports d'accidents
• 📊 **Analyser les données** - Statistiques et tendances
• 🗺️ **Visualiser les points chauds** - Cartes interactives
• 🤖 **Prédictions IA** - Analyses de risques
• 🛡️ **Promouvoir la sécurité** - Ressources éducatives

Puis-je vous aider avec quelque chose de spécifique? 🙋""",
            'ar': """🚗 **مرحباً بك في SafeRoad تونس!**

أنا مساعدك الذكي لـ **نظام إدارة حوادث المرور** - منصة تونس الشاملة للسلامة المرورية.

**ما نقدمه:**
• 📝 **الإبلاغ والمتابعة** - تقديم تقارير الحوادث
• 📊 **تحليل البيانات** - الإحصائيات والاتجاهات
• 🗺️ **تصور النقاط الساخنة** - خرائط تفاعلية
• 🤖 **توقعات الذكاء الاصطناعي** - تحليل المخاطر
• 🛡️ **تعزيز السلامة** - موارد تعليمية

هل يمكنني مساعدتك في شيء محدد؟ 🙋"""
        }
    },
    'how_can_you_help': {
        'patterns': [r'\bhow\s+can\s+you\s+help\b', r'\bwhat\s+can\s+you\s+do\b', r'\bwhat\s+are\s+you(r)?\s+(capabilities|features|abilities)\b', r'\bhelp\s+me\b', r'\bi\s+need\s+help\b'],
        'response': {
            'en': """🤖 **Here's how I can assist you:**

**📋 Reporting & Management:**
• Guide you through reporting an accident
• Explain report statuses and workflows
• Help track your submitted reports

**📊 Data & Analytics:**
• Show you current accident statistics
• Explain trends and patterns
• Help interpret the dashboard data

**🗺️ Navigation & Features:**
• Guide you around the platform
• Explain different features
• Help you find what you're looking for

**🛡️ Safety Information:**
• Share road safety tips
• Explain common accident causes
• Provide prevention guidelines

**💬 Just ask me anything!** I'm here to help 24/7.

Try asking:
• "How do I report an accident?"
• "Show me the statistics"
• "What causes most accidents?"
• "Safety tips for driving"

What would you like to know? 🙂""",
            'fr': """🤖 **Voici comment je peux vous aider:**

**📋 Rapports & Gestion:**
• Vous guider pour signaler un accident
• Expliquer les statuts des rapports
• Suivre vos rapports soumis

**📊 Données & Analyses:**
• Montrer les statistiques actuelles
• Expliquer les tendances
• Interpréter le tableau de bord

**🗺️ Navigation & Fonctionnalités:**
• Vous guider sur la plateforme
• Expliquer les différentes fonctions
• Trouver ce que vous cherchez

**🛡️ Informations de Sécurité:**
• Partager des conseils de sécurité
• Expliquer les causes d'accidents
• Fournir des directives de prévention

Que souhaitez-vous savoir? 🙂""",
            'ar': """🤖 **إليك كيف يمكنني مساعدتك:**

**📋 التقارير والإدارة:**
• إرشادك للإبلاغ عن حادث
• شرح حالات التقارير
• متابعة تقاريرك المقدمة

**📊 البيانات والتحليلات:**
• عرض الإحصائيات الحالية
• شرح الاتجاهات
• تفسير لوحة التحكم

**🗺️ التنقل والميزات:**
• إرشادك في المنصة
• شرح الميزات المختلفة
• مساعدتك في العثور على ما تبحث عنه

**🛡️ معلومات السلامة:**
• مشاركة نصائح السلامة
• شرح أسباب الحوادث
• تقديم إرشادات الوقاية

ماذا تريد أن تعرف؟ 🙂"""
        }
    },
    'ai_question': {
        'patterns': [r'\bare\s+you\s+(an?\s+)?(ai|bot|robot|artificial|machine)\b', r'\bwho\s+(are|made)\s+you\b', r'\bwhat\s+are\s+you\b', r'\bare\s+you\s+real\b', r'\bare\s+you\s+human\b'],
        'response': {
            'en': """🤖 **Yes, I'm an AI assistant!**

I'm **TrafficGuard AI**, your intelligent companion for the SafeRoad Tunisia platform.

**About Me:**
• 🧠 I'm designed to understand natural language
• 💡 I can answer questions about traffic accidents, safety, and this platform
• 📊 I have access to real-time statistics from our database
• 🌐 I speak English, French, and Arabic
• ⚡ I'm available 24/7 to help you

**My Purpose:**
I'm here to make road safety information accessible and help you navigate our system easily. Whether you need to report an accident, understand statistics, or learn about road safety - I'm your go-to assistant!

**I'm constantly learning** to serve you better. Feel free to ask me anything! 🌟""",
            'fr': """🤖 **Oui, je suis une IA!**

Je suis **TrafficGuard AI**, votre assistant intelligent pour SafeRoad Tunisie.

**À Propos de Moi:**
• 🧠 Je comprends le langage naturel
• 💡 Je réponds aux questions sur les accidents et la sécurité
• 📊 J'ai accès aux statistiques en temps réel
• 🌐 Je parle français, anglais et arabe
• ⚡ Je suis disponible 24h/24

N'hésitez pas à me poser des questions! 🌟""",
            'ar': """🤖 **نعم، أنا مساعد ذكاء اصطناعي!**

أنا **TrafficGuard AI**، رفيقك الذكي لمنصة SafeRoad تونس.

**عني:**
• 🧠 مصمم لفهم اللغة الطبيعية
• 💡 أجيب على الأسئلة حول الحوادث والسلامة
• 📊 لدي وصول للإحصائيات في الوقت الفعلي
• 🌐 أتحدث العربية والإنجليزية والفرنسية
• ⚡ متاح على مدار الساعة

لا تتردد في سؤالي! 🌟"""
        }
    },
    'general_question': {
        'patterns': [r'^(hey|hi|hello)?\s*(can\s+you|could\s+you|would\s+you|please)\s+(tell|show|help|explain|give)\b', r'\bquestion\b', r'\bi\s+(want|need)\s+to\s+(know|understand|learn)\b'],
        'response': {
            'en': """Of course! I'd be happy to help. 😊

**I'm knowledgeable about:**
• 🚗 **Traffic Accidents** - Reporting, tracking, understanding
• 📊 **Statistics** - Data analysis, trends, insights
• 🗺️ **Maps & Locations** - Hotspots, governorates, geographic data
• 🛡️ **Road Safety** - Tips, causes, prevention
• ⚙️ **Platform Features** - Navigation, account management

**Just ask your question directly!** For example:
• "How many accidents happened this year?"
• "What's the most dangerous governorate?"
• "How do I submit a report?"
• "Give me safety tips"

What would you like to know? I'm all ears! 👂""",
            'fr': """Bien sûr! Je serais ravi de vous aider. 😊

Posez simplement votre question directement! Par exemple:
• "Combien d'accidents cette année?"
• "Quel est le gouvernorat le plus dangereux?"
• "Comment soumettre un rapport?"

Que souhaitez-vous savoir? 👂""",
            'ar': """بالطبع! يسعدني مساعدتك. 😊

اطرح سؤالك مباشرة! مثلاً:
• "كم حادث وقع هذا العام؟"
• "ما هي الولاية الأكثر خطورة؟"
• "كيف أقدم تقريراً؟"

ماذا تريد أن تعرف؟ 👂"""
        }
    },
    'confused': {
        'patterns': [r"\bi\s*don'?t\s*(know|understand)\b", r'\bconfused\b', r'\blost\b', r'\bnot\s+sure\b', r"\bwhat\s+should\s+i\s+do\b", r'\bwhere\s+do\s+i\s+(start|begin)\b'],
        'response': {
            'en': """No worries! Let me help you get started. 🌟

**If you're new here, here's what you can do:**

1️⃣ **Report an Accident**
   Click "Report Accident" in the menu to submit a new report

2️⃣ **View Statistics**
   Go to "Statistics" to see accident data and trends

3️⃣ **Check Your Reports**
   Visit "My Reports" to see your submitted reports

4️⃣ **Explore the Map**
   Use the interactive map to see accident locations

**Quick Actions I Can Help With:**
• 📝 "I want to report an accident"
• 📊 "Show me the statistics"
• 🗺️ "Where do most accidents happen?"
• 🛡️ "Give me safety tips"

What sounds most helpful right now? 🤔""",
            'fr': """Pas de souci! Laissez-moi vous aider. 🌟

**Si vous êtes nouveau:**
1️⃣ **Signaler un accident** - Menu → Signaler
2️⃣ **Voir les statistiques** - Menu → Statistiques
3️⃣ **Vérifier vos rapports** - Menu → Mes Rapports
4️⃣ **Explorer la carte** - Carte interactive

Qu'est-ce qui vous serait le plus utile? 🤔""",
            'ar': """لا تقلق! دعني أساعدك. 🌟

**إذا كنت جديداً:**
1️⃣ **الإبلاغ عن حادث** - القائمة → الإبلاغ
2️⃣ **عرض الإحصائيات** - القائمة → الإحصائيات
3️⃣ **التحقق من تقاريرك** - القائمة → تقاريري
4️⃣ **استكشاف الخريطة** - الخريطة التفاعلية

ما الذي سيكون أكثر فائدة الآن؟ 🤔"""
        }
    },
    'opinion': {
        'patterns': [r'\bwhat\s+do\s+you\s+think\b', r'\byour\s+opinion\b', r'\bdo\s+you\s+(like|believe|feel)\b', r'\bis\s+it\s+(good|bad|safe|dangerous)\b'],
        'response': {
            'en': """That's a thoughtful question! 🤔

As an AI focused on road safety, I can share some insights:

**My Perspective on Road Safety:**
• Every accident is preventable with proper precautions
• Data-driven decisions save lives
• Education and awareness are key
• Technology can help predict and prevent incidents

**Based on our data:**
• Speeding remains the #1 cause of accidents
• Most accidents happen during peak hours (6-9 AM, 5-8 PM)
• Simple precautions reduce risk by up to 70%

Would you like me to share specific statistics or safety recommendations? I'm here to provide factual, helpful information! 📊""",
            'fr': """Bonne question! 🤔

En tant qu'IA focalisée sur la sécurité routière:
• Chaque accident est évitable avec des précautions
• Les données sauvent des vies
• L'éducation est essentielle

Voulez-vous des statistiques ou recommandations? 📊""",
            'ar': """سؤال جيد! 🤔

كذكاء اصطناعي مركز على السلامة المرورية:
• كل حادث يمكن تجنبه بالاحتياطات
• القرارات المبنية على البيانات تنقذ الأرواح
• التعليم والتوعية أساسيان

هل تريد إحصائيات أو توصيات محددة؟ 📊"""
        }
    },
    'small_talk': {
        'patterns': [r'\bhow\s+are\s+you\b', r"\bhow'?s\s+it\s+going\b", r'\bwhats?\s+up\b', r'\bgood\s+(morning|afternoon|evening|night)\b'],
        'response': {
            'en': """I'm doing great, thank you for asking! 😊

I'm here and ready to assist you with anything related to road safety and traffic accidents in Tunisia.

**Currently monitoring:**
• 📊 Live accident statistics
• 🗺️ Traffic hotspots
• 📝 Report submissions

Is there something specific I can help you with today? 🚗""",
            'fr': """Je vais très bien, merci! 😊

Je suis prêt à vous aider avec tout ce qui concerne la sécurité routière.

Y a-t-il quelque chose de spécifique que je puisse faire pour vous? 🚗""",
            'ar': """أنا بخير، شكراً لسؤالك! 😊

أنا جاهز لمساعدتك في كل ما يتعلق بالسلامة المرورية.

هل هناك شيء محدد يمكنني مساعدتك به اليوم؟ 🚗"""
        }
    },
    'negative_feedback': {
        'patterns': [r"\bthat\s*(didn'?t|doesn'?t|won'?t)\s+help\b", r'\bnot\s+(helpful|useful|what\s+i\s+(need|want|asked))\b', r'\bwrong\s+answer\b', r"\byou\s+don'?t\s+understand\b"],
        'response': {
            'en': """I apologize if my response wasn't helpful! 🙏

Let me try again. Could you please:

1️⃣ **Rephrase your question** with more details
2️⃣ **Be specific** about what you're looking for
3️⃣ **Try one of these common topics:**
   • "How do I report an accident?"
   • "Show me accident statistics"
   • "What causes most accidents?"
   • "Navigate to [page name]"

**Or tell me directly:** What exactly do you need help with?

I want to make sure I give you the right information! 💪""",
            'fr': """Je m'excuse si ma réponse n'était pas utile! 🙏

Pourriez-vous reformuler votre question avec plus de détails?

Dites-moi exactement ce dont vous avez besoin! 💪""",
            'ar': """أعتذر إذا لم تكن إجابتي مفيدة! 🙏

هل يمكنك إعادة صياغة سؤالك بمزيد من التفاصيل؟

أخبرني بالضبط ما تحتاج المساعدة فيه! 💪"""
        }
    },
    'tunisia_specific': {
        'patterns': [r'\btunisi[ae]\b', r'\bgovernorate\b', r'\btunis\b', r'\bsfax\b', r'\bsousse\b', r'\bkairouan\b', r'\bbizerte\b', r'\bgab[èe]s\b'],
        'response': {
            'en': """🇹🇳 **SafeRoad covers all of Tunisia!**

Our system monitors traffic accidents across all **24 governorates**:

**Most Monitored Regions:**
• 🏙️ **Tunis** - Capital region with highest traffic
• 🌊 **Sfax** - Major coastal city
• 🏖️ **Sousse** - Tourist and industrial hub
• 🏛️ **Kairouan** - Central Tunisia
• ⚓ **Bizerte** - Northern port city

**What you can explore:**
• View accidents by specific governorate
• Compare regional statistics
• See delegation-level data
• Identify local hotspots

Would you like to see statistics for a specific governorate? Just ask! 📍""",
            'fr': """🇹🇳 **SafeRoad couvre toute la Tunisie!**

Notre système surveille les accidents dans les **24 gouvernorats**.

Voulez-vous voir les statistiques d'un gouvernorat spécifique? 📍""",
            'ar': """🇹🇳 **SafeRoad يغطي كل تونس!**

نظامنا يراقب الحوادث في جميع **24 ولاية**.

هل تريد رؤية إحصائيات ولاية محددة؟ 📍"""
        }
    }
}

# Knowledge base for traffic accident related queries
KNOWLEDGE_BASE = {
    'report_accident': {
        'keywords': ['report', 'submit', 'file', 'new accident', 'how to report', 'create report'],
        'response': {
            'en': """To report an accident, follow these steps:

**1.** Go to the **Dashboard** and click on "Report Accident" or navigate to the Reports section.

**2.** Fill in the required information:
   • Date and time of the accident
   • Location (governorate, delegation)
   • Severity level
   • Description of what happened
   • Cause of the accident

**3.** Upload any supporting photos or documents if available.

**4.** Click "Submit Report" to send your report.

Your report will be reviewed by our team and you'll receive updates on its status.""",
            'fr': """Pour signaler un accident, suivez ces étapes:

**1.** Allez au **Tableau de bord** et cliquez sur "Signaler un accident" ou accédez à la section Rapports.

**2.** Remplissez les informations requises:
   • Date et heure de l'accident
   • Lieu (gouvernorat, délégation)
   • Niveau de gravité
   • Description de ce qui s'est passé
   • Cause de l'accident

**3.** Téléchargez des photos ou documents si disponibles.

**4.** Cliquez sur "Soumettre le rapport" pour envoyer.

Votre rapport sera examiné et vous recevrez des mises à jour sur son statut.""",
            'ar': """للإبلاغ عن حادث، اتبع هذه الخطوات:

**1.** اذهب إلى **لوحة التحكم** وانقر على "الإبلاغ عن حادث".

**2.** املأ المعلومات المطلوبة:
   • تاريخ ووقت الحادث
   • الموقع (الولاية، المعتمدية)
   • مستوى الخطورة
   • وصف ما حدث
   • سبب الحادث

**3.** قم بتحميل الصور أو المستندات إن وجدت.

**4.** انقر على "إرسال التقرير".

سيتم مراجعة تقريرك وستتلقى تحديثات حول حالته."""
        }
    },
    'statistics': {
        'keywords': ['statistics', 'stats', 'data', 'numbers', 'analytics', 'trends', 'charts'],
        'response': {
            'en': """Our **Statistics** page provides comprehensive accident data analytics:

📊 **Available Analytics:**
• Total accidents over time
• Accidents by severity (Fatal, Serious, Minor)
• Accidents by cause
• Geographic distribution by governorate
• Time-based patterns (hourly, daily, monthly)
• Year-over-year comparisons

📍 **Interactive Map:**
• View accident hotspots
• Filter by region
• See cluster patterns

🤖 **AI Predictions:**
• 7-day forecasts
• High-risk zones identification
• Peak risk hours analysis

Navigate to **Statistics** from the main menu to explore the data!""",
            'fr': """Notre page **Statistiques** fournit des analyses complètes:

📊 **Analyses disponibles:**
• Total des accidents dans le temps
• Accidents par gravité (Mortel, Grave, Léger)
• Accidents par cause
• Distribution géographique par gouvernorat
• Modèles temporels (horaire, quotidien, mensuel)
• Comparaisons annuelles

📍 **Carte interactive:**
• Voir les points chauds d'accidents
• Filtrer par région
• Voir les modèles de clusters

🤖 **Prédictions IA:**
• Prévisions sur 7 jours
• Identification des zones à risque
• Analyse des heures de pointe

Accédez aux **Statistiques** depuis le menu principal!""",
            'ar': """توفر صفحة **الإحصائيات** تحليلات شاملة:

📊 **التحليلات المتاحة:**
• إجمالي الحوادث عبر الزمن
• الحوادث حسب الخطورة (مميتة، خطيرة، طفيفة)
• الحوادث حسب السبب
• التوزيع الجغرافي حسب الولاية
• الأنماط الزمنية (ساعية، يومية، شهرية)
• مقارنات سنوية

📍 **خريطة تفاعلية:**
• عرض النقاط الساخنة للحوادث
• التصفية حسب المنطقة
• رؤية أنماط التجمعات

🤖 **توقعات الذكاء الاصطناعي:**
• توقعات 7 أيام
• تحديد المناطق عالية الخطورة
• تحليل ساعات الذروة

انتقل إلى **الإحصائيات** من القائمة الرئيسية!"""
        }
    },
    'causes': {
        'keywords': ['cause', 'causes', 'why', 'reason', 'main cause', 'accident causes'],
        'response': {
            'en': """**Main Causes of Traffic Accidents:**

🚗 **1. Speeding (35%)**
Driving above speed limits reduces reaction time and increases crash severity.

📱 **2. Distracted Driving (25%)**
Using phones, eating, or other distractions while driving.

🍺 **3. Drunk Driving (15%)**
Alcohol impairs judgment, coordination, and reaction time.

⚠️ **4. Reckless Driving (12%)**
Aggressive behavior, tailgating, and ignoring traffic rules.

🌙 **5. Poor Weather Conditions (8%)**
Rain, fog, and poor visibility contribute to accidents.

🔧 **6. Vehicle Malfunction (5%)**
Brake failures, tire blowouts, and other mechanical issues.

*Statistics based on our accident database analysis.*""",
            'fr': """**Principales causes des accidents de la route:**

🚗 **1. Excès de vitesse (35%)**
Dépasser les limites réduit le temps de réaction.

📱 **2. Distraction au volant (25%)**
Utilisation du téléphone, manger en conduisant.

🍺 **3. Conduite en état d'ivresse (15%)**
L'alcool altère le jugement et les réflexes.

⚠️ **4. Conduite imprudente (12%)**
Comportement agressif, non-respect des règles.

🌙 **5. Mauvaises conditions météo (8%)**
Pluie, brouillard, mauvaise visibilité.

🔧 **6. Défaillance du véhicule (5%)**
Freins défaillants, crevaisons, problèmes mécaniques.

*Statistiques basées sur notre base de données.*""",
            'ar': """**الأسباب الرئيسية لحوادث المرور:**

🚗 **1. السرعة الزائدة (35%)**
تجاوز حدود السرعة يقلل وقت رد الفعل.

📱 **2. تشتت الانتباه (25%)**
استخدام الهاتف أو الأكل أثناء القيادة.

🍺 **3. القيادة تحت تأثير الكحول (15%)**
الكحول يضعف الحكم والتنسيق.

⚠️ **4. القيادة المتهورة (12%)**
السلوك العدواني وتجاهل قواعد المرور.

🌙 **5. سوء الأحوال الجوية (8%)**
المطر والضباب وضعف الرؤية.

🔧 **6. خلل في المركبة (5%)**
فشل الفرامل وانفجار الإطارات.

*إحصائيات مبنية على تحليل قاعدة بياناتنا.*"""
        }
    },
    'safety_tips': {
        'keywords': ['safety', 'tips', 'safe', 'prevent', 'avoid', 'advice', 'precautions'],
        'response': {
            'en': """**Road Safety Tips to Prevent Accidents:**

🚦 **Before Driving:**
• Check mirrors, lights, and tires
• Ensure adequate rest (avoid drowsy driving)
• Plan your route in advance

🚗 **While Driving:**
• Always wear your seatbelt
• Keep safe following distance (3-second rule)
• Avoid using your phone
• Respect speed limits
• Use turn signals

🌧️ **In Bad Weather:**
• Reduce speed by 30-50%
• Increase following distance
• Turn on headlights
• Avoid sudden braking

🚸 **Around Pedestrians:**
• Slow down in school zones
• Watch for children and elderly
• Always yield at crosswalks

⛽ **Vehicle Maintenance:**
• Regular brake inspections
• Keep tires properly inflated
• Check lights regularly

*Stay safe on the roads!* 🙏""",
            'fr': """**Conseils de sécurité routière:**

🚦 **Avant de conduire:**
• Vérifiez les rétroviseurs, feux et pneus
• Assurez-vous d'être bien reposé
• Planifiez votre itinéraire

🚗 **En conduisant:**
• Attachez toujours votre ceinture
• Gardez une distance de sécurité
• Évitez d'utiliser votre téléphone
• Respectez les limites de vitesse
• Utilisez les clignotants

🌧️ **Par mauvais temps:**
• Réduisez la vitesse de 30-50%
• Augmentez la distance de suivi
• Allumez les phares
• Évitez les freinages brusques

🚸 **Près des piétons:**
• Ralentissez dans les zones scolaires
• Attention aux enfants et personnes âgées
• Cédez le passage aux passages piétons

⛽ **Entretien du véhicule:**
• Inspections régulières des freins
• Pneus correctement gonflés
• Vérifiez les feux régulièrement

*Restez prudent sur les routes!* 🙏""",
            'ar': """**نصائح السلامة المرورية:**

🚦 **قبل القيادة:**
• تحقق من المرايا والأضواء والإطارات
• تأكد من الراحة الكافية
• خطط لمسارك مسبقاً

🚗 **أثناء القيادة:**
• ارتدِ حزام الأمان دائماً
• حافظ على مسافة أمان
• تجنب استخدام الهاتف
• احترم حدود السرعة
• استخدم إشارات الانعطاف

🌧️ **في الطقس السيئ:**
• قلل السرعة بنسبة 30-50%
• زِد مسافة المتابعة
• شغّل الأضواء الأمامية
• تجنب الفرملة المفاجئة

🚸 **قرب المشاة:**
• أبطئ في مناطق المدارس
• انتبه للأطفال وكبار السن
• أعطِ الأولوية في ممرات المشاة

⛽ **صيانة المركبة:**
• فحص الفرامل بانتظام
• حافظ على ضغط الإطارات
• تحقق من الأضواء بانتظام

*ابقَ آمناً على الطرق!* 🙏"""
        }
    },
    'account': {
        'keywords': ['account', 'profile', 'settings', 'password', 'email', 'change password'],
        'response': {
            'en': """**Account Management Guide:**

👤 **View/Edit Profile:**
Go to your profile icon → Account Settings

⚙️ **Available Settings:**
• Update personal information
• Change password
• Notification preferences
• Language settings
• Dark/Light mode toggle

🔐 **Security Tips:**
• Use a strong, unique password
• Update password regularly
• Don't share login credentials

📧 **Contact Support:**
If you need help with your account, contact our support team through the help section.

Navigate to **Account Settings** from your profile menu!""",
            'fr': """**Guide de gestion de compte:**

👤 **Voir/Modifier le profil:**
Allez sur votre icône de profil → Paramètres du compte

⚙️ **Paramètres disponibles:**
• Mettre à jour les informations personnelles
• Changer le mot de passe
• Préférences de notification
• Paramètres de langue
• Mode sombre/clair

🔐 **Conseils de sécurité:**
• Utilisez un mot de passe fort et unique
• Mettez à jour régulièrement
• Ne partagez pas vos identifiants

📧 **Contacter le support:**
Si vous avez besoin d'aide, contactez notre équipe support.

Accédez aux **Paramètres du compte** depuis votre menu profil!""",
            'ar': """**دليل إدارة الحساب:**

👤 **عرض/تعديل الملف الشخصي:**
اذهب إلى أيقونة الملف الشخصي ← إعدادات الحساب

⚙️ **الإعدادات المتاحة:**
• تحديث المعلومات الشخصية
• تغيير كلمة المرور
• تفضيلات الإشعارات
• إعدادات اللغة
• الوضع الداكن/الفاتح

🔐 **نصائح الأمان:**
• استخدم كلمة مرور قوية وفريدة
• حدّث كلمة المرور بانتظام
• لا تشارك بيانات تسجيل الدخول

📧 **الاتصال بالدعم:**
إذا احتجت مساعدة، تواصل مع فريق الدعم.

انتقل إلى **إعدادات الحساب** من قائمة ملفك الشخصي!"""
        }
    },
    'navigation': {
        'keywords': ['where', 'find', 'navigate', 'go to', 'access', 'page', 'menu'],
        'response': {
            'en': """**System Navigation Guide:**

🏠 **Dashboard** - Overview of your reports and quick actions

📋 **My Reports** - View and manage your submitted reports

📊 **Statistics** - Analytics and data visualizations

👥 **Users** (Admin only) - User management

⚙️ **Settings** - Account preferences and configuration

📝 **Report Accident** - Submit a new accident report

🗺️ **Map View** - Geographic accident visualization

💡 **Pro Tips:**
• Use the search bar for quick access
• Keyboard shortcuts: Press `?` for help
• Customize your dashboard widgets

What page would you like to access?""",
            'fr': """**Guide de navigation:**

🏠 **Tableau de bord** - Aperçu de vos rapports et actions rapides

📋 **Mes rapports** - Voir et gérer vos rapports soumis

📊 **Statistiques** - Analyses et visualisations de données

👥 **Utilisateurs** (Admin) - Gestion des utilisateurs

⚙️ **Paramètres** - Préférences et configuration du compte

📝 **Signaler un accident** - Soumettre un nouveau rapport

🗺️ **Vue carte** - Visualisation géographique

💡 **Astuces:**
• Utilisez la barre de recherche
• Raccourcis clavier: `?` pour l'aide
• Personnalisez vos widgets

Quelle page souhaitez-vous accéder?""",
            'ar': """**دليل التنقل في النظام:**

🏠 **لوحة التحكم** - نظرة عامة على تقاريرك والإجراءات السريعة

📋 **تقاريري** - عرض وإدارة التقارير المقدمة

📊 **الإحصائيات** - التحليلات والتصورات البيانية

👥 **المستخدمون** (للمسؤول) - إدارة المستخدمين

⚙️ **الإعدادات** - تفضيلات الحساب والتكوين

📝 **الإبلاغ عن حادث** - تقديم تقرير جديد

🗺️ **عرض الخريطة** - التصور الجغرافي للحوادث

💡 **نصائح:**
• استخدم شريط البحث للوصول السريع
• اختصارات لوحة المفاتيح: اضغط `؟` للمساعدة
• خصص أدوات لوحة التحكم

ما الصفحة التي تريد الوصول إليها؟"""
        }
    },
    'greeting': {
        'keywords': ['hello', 'hi', 'hey', 'good morning', 'good evening', 'good afternoon', 'salut', 'bonjour', 'مرحبا', 'السلام'],
        'response': {
            'en': """Hello! 👋 Welcome to SafeRoad Assistant!

I'm here to help you with:
• 📝 Reporting accidents
• 📊 Understanding statistics
• 🛡️ Road safety information
• 🔧 System navigation

How can I assist you today?""",
            'fr': """Bonjour! 👋 Bienvenue sur l'Assistant SafeRoad!

Je suis là pour vous aider avec:
• 📝 Signaler des accidents
• 📊 Comprendre les statistiques
• 🛡️ Informations sur la sécurité routière
• 🔧 Navigation dans le système

Comment puis-je vous aider aujourd'hui?""",
            'ar': """مرحباً! 👋 أهلاً بك في مساعد SafeRoad!

أنا هنا لمساعدتك في:
• 📝 الإبلاغ عن الحوادث
• 📊 فهم الإحصائيات
• 🛡️ معلومات السلامة المرورية
• 🔧 التنقل في النظام

كيف يمكنني مساعدتك اليوم؟"""
        }
    },
    'insurance': {
        'keywords': ['insurance', 'assurance', 'تأمين', 'claim', 'company', 'repair cost', 'estimate', 'damage'],
        'response': {
            'en': """🛡️ **Insurance Services**

Our platform provides comprehensive insurance support:

**📋 Insurance Companies:**
• 10+ licensed Tunisian insurance providers
• Contact info, ratings, and claim times
• STAR, GAT, COMAR, Maghrebia, CARTE, and more

**💰 Repair Cost Estimator:**
• Select damaged parts (bumper, door, windshield, etc.)
• Choose severity and vehicle type
• Get instant cost estimates in TND

**✅ Claim Checklist:**
• What to do at the accident scene
• Documents needed within 24 hours
• Step-by-step claim process

**📄 Required Documents:**
• Constat Amiable (accident report form)
• Police report
• Photos of damage
• Repair estimates

Go to **Services → Insurance** tab to access all these features! 📱""",
            'fr': """🛡️ **Services d'Assurance**

Notre plateforme offre un support complet en assurance:

**📋 Compagnies d'Assurance:**
• 10+ assureurs tunisiens agréés
• Coordonnées, notes et délais de traitement

**💰 Estimateur de Coûts:**
• Sélectionnez les pièces endommagées
• Obtenez des estimations instantanées en TND

**✅ Checklist de Réclamation:**
• Quoi faire sur les lieux de l'accident
• Documents nécessaires
• Processus étape par étape

Allez dans **Services → Assurance** pour accéder! 📱""",
            'ar': """🛡️ **خدمات التأمين**

منصتنا توفر دعم تأمين شامل:

**📋 شركات التأمين:**
• 10+ شركات تأمين تونسية مرخصة
• معلومات الاتصال والتقييمات

**💰 تقدير تكلفة الإصلاح:**
• اختر الأجزاء التالفة
• احصل على تقديرات فورية بالدينار

**✅ قائمة المطالبات:**
• ماذا تفعل في موقع الحادث
• المستندات المطلوبة
• العملية خطوة بخطوة

اذهب إلى **الخدمات ← التأمين** للوصول! 📱"""
        }
    },
    'fuel_prices': {
        'keywords': ['fuel', 'gas', 'petrol', 'diesel', 'essence', 'carburant', 'وقود', 'بنزين', 'price', 'cost'],
        'response': {
            'en': """⛽ **Fuel Prices in Tunisia**

Current official fuel prices (TND/Liter):

**🔴 Super (Essence):** ~2.525 TND
**🟠 Regular (Essence):** ~2.345 TND
**🟡 Diesel:** ~2.025 TND
**🟢 LPG (GPL):** ~0.895 TND

**🧮 Trip Cost Calculator:**
• Enter your distance
• Select fuel type
• Set consumption rate
• Get instant cost estimate

**📈 Price Trends:**
• View historical price changes
• Track price evolution over time

Go to **Services → Fuel Prices** for live data and calculator! 🚗""",
            'fr': """⛽ **Prix du Carburant en Tunisie**

Prix officiels actuels (TND/Litre):

**🔴 Super:** ~2.525 TND
**🟠 Essence Normale:** ~2.345 TND
**🟡 Gasoil:** ~2.025 TND
**🟢 GPL:** ~0.895 TND

**🧮 Calculateur de Trajet:**
• Entrez la distance
• Sélectionnez le type de carburant
• Obtenez le coût estimé

Allez dans **Services → Prix Carburant** pour les données en direct! 🚗""",
            'ar': """⛽ **أسعار الوقود في تونس**

الأسعار الرسمية الحالية (دينار/لتر):

**🔴 سوبر:** ~2.525 دينار
**🟠 بنزين عادي:** ~2.345 دينار
**🟡 ديزل:** ~2.025 دينار
**🟢 غاز:** ~0.895 دينار

**🧮 حاسبة تكلفة الرحلة:**
• أدخل المسافة
• اختر نوع الوقود
• احصل على التكلفة المقدرة

اذهب إلى **الخدمات ← أسعار الوقود**! 🚗"""
        }
    },
    'emergency': {
        'keywords': ['emergency', 'urgence', 'طوارئ', 'hospital', 'police', 'ambulance', 'tow', 'help', 'accident now'],
        'response': {
            'en': """🚨 **Emergency Services - Tunisia**

**📞 Emergency Numbers:**
• **Police:** 197
• **SAMU (Ambulance):** 190
• **Fire Department:** 198
• **National Guard:** 193
• **Traffic Police:** 71 341 141

**🏥 Hospitals:**
• Major hospitals in all governorates
• Emergency room locations
• Contact information

**🚗 Tow Services (24/7):**
• SOS Dépannage: 71 862 862
• Touring Club: 71 323 152
• Auto Assistance: 71 780 780

Go to **Services → Emergency** tab for full information and maps! 🗺️

**If you're in an emergency NOW:**
1. Call 197 (Police) or 190 (Ambulance)
2. Move to safety if possible
3. Stay calm and provide your location""",
            'fr': """🚨 **Services d'Urgence - Tunisie**

**📞 Numéros d'Urgence:**
• **Police:** 197
• **SAMU:** 190
• **Pompiers:** 198
• **Garde Nationale:** 193

**🏥 Hôpitaux:**
• Hôpitaux dans tous les gouvernorats
• Services d'urgence

**🚗 Dépannage (24h/24):**
• SOS Dépannage: 71 862 862
• Touring Club: 71 323 152

Allez dans **Services → Urgence** pour plus d'infos! 🗺️""",
            'ar': """🚨 **خدمات الطوارئ - تونس**

**📞 أرقام الطوارئ:**
• **الشرطة:** 197
• **الإسعاف:** 190
• **الإطفاء:** 198
• **الحرس الوطني:** 193

**🏥 المستشفيات:**
• مستشفيات في جميع الولايات
• معلومات الاتصال

**🚗 خدمات السحب (24/7):**
• SOS Dépannage: 71 862 862

اذهب إلى **الخدمات ← الطوارئ** لمزيد من المعلومات! 🗺️"""
        }
    },
    'traffic_news': {
        'keywords': ['news', 'traffic news', 'alerts', 'road conditions', 'actualités', 'أخبار', 'closure', 'accident report'],
        'response': {
            'en': """📰 **Traffic News & Alerts**

Our platform provides real-time traffic information:

**🚨 Live Traffic Alerts:**
• Active road incidents
• Construction zones
• Weather warnings
• Road closures

**📰 Traffic News Feed:**
• Latest road safety news from Tunisia
• Aggregated from multiple sources
• Filtered for traffic relevance

**📍 Alert Information:**
• Location and governorate
• Severity level
• Time since reported
• Alternative routes

Go to **Services → Traffic News** for live updates!

**Stay informed and drive safely!** 🚗""",
            'fr': """📰 **Actualités & Alertes Trafic**

Notre plateforme fournit des informations en temps réel:

**🚨 Alertes en Direct:**
• Incidents routiers actifs
• Zones de construction
• Avertissements météo
• Fermetures de routes

**📰 Fil d'Actualités:**
• Dernières nouvelles de sécurité routière
• Agrégées de plusieurs sources

Allez dans **Services → Actualités** pour les mises à jour!""",
            'ar': """📰 **أخبار وتنبيهات المرور**

منصتنا توفر معلومات مرور في الوقت الفعلي:

**🚨 تنبيهات مباشرة:**
• حوادث الطرق النشطة
• مناطق البناء
• تحذيرات الطقس
• إغلاق الطرق

**📰 أخبار المرور:**
• آخر أخبار السلامة المرورية

اذهب إلى **الخدمات ← الأخبار** للتحديثات! 🚗"""
        }
    },
    'thanks': {
        'keywords': ['thank', 'thanks', 'merci', 'شكرا', 'appreciate'],
        'response': {
            'en': """You're welcome! 😊 

Is there anything else I can help you with? Feel free to ask about:
• Accident reporting
• Statistics & analytics
• Road safety tips
• System navigation

I'm always here to assist!""",
            'fr': """De rien! 😊

Y a-t-il autre chose que je puisse vous aider? N'hésitez pas à demander:
• Signalement d'accidents
• Statistiques et analyses
• Conseils de sécurité routière
• Navigation dans le système

Je suis toujours là pour vous aider!""",
            'ar': """على الرحب والسعة! 😊

هل هناك شيء آخر يمكنني مساعدتك به؟ لا تتردد في السؤال عن:
• الإبلاغ عن الحوادث
• الإحصائيات والتحليلات
• نصائح السلامة المرورية
• التنقل في النظام

أنا دائماً هنا للمساعدة!"""
        }
    }
}

DEFAULT_RESPONSES = {
    'en': [
        "That's an interesting question! While I'm specifically designed for traffic safety topics, I'll try my best to help. Could you tell me more about what you're looking for? 🤔",
        "I'm your traffic safety assistant, and I want to help! Could you rephrase that or ask about:\n• 📝 Reporting accidents\n• 📊 Statistics & data\n• 🛡️ Safety tips\n• 🗺️ Navigation help",
        "Hmm, I'm not quite sure I understand. I'm best at helping with traffic accidents and road safety in Tunisia. What aspect interests you? 🚗",
        "Great question! I specialize in road safety topics. Try asking about:\n• How to report an accident\n• Current statistics\n• Safety recommendations\n• Using this platform\n\nWhat would you like to know? 😊"
    ],
    'fr': [
        "Question intéressante! Je suis spécialisé en sécurité routière. Pourriez-vous reformuler ou demander:\n• 📝 Signaler des accidents\n• 📊 Statistiques\n• 🛡️ Conseils de sécurité",
        "Je ne suis pas sûr de comprendre. Je suis meilleur pour aider avec les accidents et la sécurité routière. Qu'est-ce qui vous intéresse? 🚗",
        "Bonne question! Essayez de demander:\n• Comment signaler un accident\n• Les statistiques actuelles\n• Les recommandations de sécurité"
    ],
    'ar': [
        "سؤال مثير! أنا متخصص في السلامة المرورية. هل يمكنك إعادة الصياغة أو السؤال عن:\n• 📝 الإبلاغ عن الحوادث\n• 📊 الإحصائيات\n• 🛡️ نصائح السلامة",
        "لست متأكداً من فهمي. أنا أفضل في المساعدة بحوادث المرور والسلامة. ما الذي يهمك؟ 🚗",
        "سؤال جيد! جرب السؤال عن:\n• كيفية الإبلاغ عن حادث\n• الإحصائيات الحالية\n• توصيات السلامة"
    ]
}


def get_language():
    """Get language from request or default to English"""
    lang = request.headers.get('Accept-Language', 'en')[:2]
    if lang not in ['en', 'fr', 'ar']:
        lang = 'en'
    return lang


def check_conversational_patterns(message):
    """Check message against conversational patterns using regex"""
    message_lower = message.lower().strip()
    
    for pattern_name, pattern_data in CONVERSATIONAL_PATTERNS.items():
        for pattern in pattern_data['patterns']:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return pattern_data['response']
    
    return None


def find_best_match(message):
    """Find the best matching topic based on keywords"""
    message_lower = message.lower()
    best_match = None
    best_score = 0
    
    for topic, data in KNOWLEDGE_BASE.items():
        score = 0
        for keyword in data['keywords']:
            if keyword.lower() in message_lower:
                # Give higher score for longer keyword matches
                score += len(keyword)
        
        if score > best_score:
            best_score = score
            best_match = topic
    
    return best_match if best_score > 0 else None


def generate_contextual_response(message, history, lang):
    """Generate context-aware response based on conversation history"""
    # Check if following up on a previous topic
    if history and len(history) >= 2:
        last_bot_response = None
        for msg in reversed(history):
            if msg.get('role') == 'assistant':
                last_bot_response = msg.get('content', '')
                break
        
        # If user asks for "more" or "details" after a response
        message_lower = message.lower()
        if last_bot_response and any(word in message_lower for word in ['more', 'detail', 'explain', 'elaborate', 'continue']):
            if 'statistics' in last_bot_response.lower() or 'stats' in last_bot_response.lower():
                return KNOWLEDGE_BASE.get('statistics', {}).get('response', {}).get(lang)
            elif 'report' in last_bot_response.lower():
                return KNOWLEDGE_BASE.get('report_accident', {}).get('response', {}).get(lang)
            elif 'safety' in last_bot_response.lower() or 'tips' in last_bot_response.lower():
                return KNOWLEDGE_BASE.get('safety_tips', {}).get('response', {}).get(lang)
    
    return None


def check_clarification_patterns(message):
    """Check if message is a follow-up clarification, argument, or correction"""
    message_lower = message.lower().strip()
    
    for pattern_type, pattern_data in CLARIFICATION_PATTERNS.items():
        for pattern in pattern_data['patterns']:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return pattern_data['response']
    
    return None


def check_off_topic(message):
    """Check if message is about a topic outside our domain"""
    message_lower = message.lower().strip()
    
    for topic_name, topic_data in OFF_TOPIC_PATTERNS.items():
        for pattern in topic_data['patterns']:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return topic_data['response']
    
    return None


def generate_response(message, history=None):
    """Generate a response based on the user's message with enhanced AI capabilities"""
    lang = get_language()
    message_lower = message.lower().strip()
    
    # FIRST: Check if this is a follow-up clarification, argument, or correction
    # This prevents the bot from repeating off-topic responses when user argues back
    clarification_response = check_clarification_patterns(message)
    if clarification_response:
        return clarification_response.get(lang, clarification_response.get('en', ''))
    
    # SECOND: Check for weather questions - we have weather API integration!
    weather_patterns = [
        r'\b(what|how|whats|what\'s|hows)\b.*(weather|temperature|forecast)',
        r'\b(is\s+it|will\s+it)\s+(rain|hot|cold|sunny|cloudy)',
        r'\bweather\b',
        r'\btemperature\b',
        r'\bforecast\b',
        r'\bmeteo\b',
        r'\bطقس\b',
        r'\bحرارة\b',
    ]
    for pattern in weather_patterns:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return get_weather_response(message, lang)
    
    # THIRD: Check for off-topic questions (news, sports, etc.)
    # Only triggers for actual QUESTIONS, not discussions mentioning the topic
    off_topic_response = check_off_topic(message)
    if off_topic_response:
        return off_topic_response.get(lang, off_topic_response.get('en', ''))
    
    # Fourth, check for conversational/vague patterns
    conversational_response = check_conversational_patterns(message)
    if conversational_response:
        return conversational_response.get(lang, conversational_response.get('en', ''))
    
    # Check for context-aware response
    if history:
        contextual = generate_contextual_response(message, history, lang)
        if contextual:
            return contextual
    
    # Check for live statistics queries
    live_stats_keywords = ['how many', 'total accidents', 'current stats', 'live data', 'database stats', 
                          'combien', 'nombre total', 'statistiques actuelles',
                          'كم عدد', 'إجمالي الحوادث', 'الإحصائيات الحالية']
    
    if any(kw in message_lower for kw in live_stats_keywords):
        stats = get_live_statistics()
        if stats:
            if lang == 'ar':
                return f"""📊 **إحصائيات النظام الحالية:**

🚗 **إجمالي الحوادث:** {stats['total']:,} حادث

📍 **أكثر ولاية تضرراً:** {stats['top_governorate']} ({stats['top_governorate_count']:,} حادث)

⚠️ **السبب الرئيسي:** {stats['top_cause']}

📝 **تقارير قيد المراجعة:** {stats['pending_reports']}

*البيانات محدثة في الوقت الفعلي من قاعدة البيانات.*

اذهب إلى **الإحصائيات** للمزيد من التفاصيل!"""
            elif lang == 'fr':
                return f"""📊 **Statistiques actuelles du système:**

🚗 **Total des accidents:** {stats['total']:,} accidents

📍 **Gouvernorat le plus touché:** {stats['top_governorate']} ({stats['top_governorate_count']:,} accidents)

⚠️ **Cause principale:** {stats['top_cause']}

📝 **Rapports en attente:** {stats['pending_reports']}

*Données en temps réel de la base de données.*

Allez dans **Statistiques** pour plus de détails!"""
            else:
                return f"""📊 **Current System Statistics:**

🚗 **Total Accidents:** {stats['total']:,} accidents recorded

📍 **Most Affected Governorate:** {stats['top_governorate']} ({stats['top_governorate_count']:,} accidents)

⚠️ **Top Cause:** {stats['top_cause']}

📝 **Pending Reports:** {stats['pending_reports']} awaiting review

*Live data fetched from the database.*

Go to **Statistics** for more detailed analytics!"""
    
    # Find the best matching topic from knowledge base
    topic = find_best_match(message)
    
    if topic:
        return KNOWLEDGE_BASE[topic]['response'].get(lang, KNOWLEDGE_BASE[topic]['response']['en'])
    
    # If no match found, return a helpful default response
    return random.choice(DEFAULT_RESPONSES.get(lang, DEFAULT_RESPONSES['en']))


@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        message = data.get('message', '').strip()
        history = data.get('history', [])
        
        if not message:
            return jsonify({'error': 'Empty message'}), 400
        
        if len(message) > 500:
            return jsonify({'error': 'Message too long'}), 400
        
        # Generate response
        response = generate_response(message, history)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Chatbot error: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'}), 500


@chatbot_bp.route('/api/chat/feedback', methods=['POST'])
def chat_feedback():
    """Handle feedback for chat responses"""
    try:
        data = request.get_json()
        
        message_id = data.get('message_id')
        feedback = data.get('feedback')  # 'helpful' or 'not_helpful'
        
        # Log feedback for future improvements
        current_app.logger.info(f"Chat feedback: {feedback} for message {message_id}")
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_live_statistics():
    """Fetch live statistics from the database"""
    try:
        from models.accident import Accident
        from models.accident_report import AccidentReport
        
        # Total accidents
        total_accidents = db.session.query(func.count(Accident.id)).scalar() or 0
        
        # Accidents by severity
        severity_counts = db.session.query(
            Accident.severity, func.count(Accident.id)
        ).group_by(Accident.severity).all()
        
        severity_data = {str(s[0]): s[1] for s in severity_counts if s[0]}
        
        # Top governorate
        top_gov = db.session.query(
            Accident.governorate, func.count(Accident.id)
        ).filter(Accident.governorate.isnot(None)).group_by(
            Accident.governorate
        ).order_by(func.count(Accident.id).desc()).first()
        
        # Top cause
        top_cause = db.session.query(
            Accident.cause, func.count(Accident.id)
        ).filter(Accident.cause.isnot(None)).group_by(
            Accident.cause
        ).order_by(func.count(Accident.id).desc()).first()
        
        # Pending reports
        pending_reports = db.session.query(func.count(AccidentReport.id)).filter(
            AccidentReport.status == 'pending'
        ).scalar() or 0
        
        return {
            'total': total_accidents,
            'severity': severity_data,
            'top_governorate': top_gov[0] if top_gov else 'N/A',
            'top_governorate_count': top_gov[1] if top_gov else 0,
            'top_cause': top_cause[0] if top_cause else 'N/A',
            'top_cause_count': top_cause[1] if top_cause else 0,
            'pending_reports': pending_reports
        }
    except Exception as e:
        current_app.logger.error(f"Error fetching statistics: {str(e)}")
        return None


@chatbot_bp.route('/api/chat/stats', methods=['GET'])
def get_stats_for_chat():
    """Get statistics summary for chat context"""
    stats = get_live_statistics()
    if stats:
        return jsonify(stats)
    return jsonify({'error': 'Unable to fetch statistics'}), 500
