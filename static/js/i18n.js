/**
 * Internationalization (i18n) System
 * Supports English, French, and Arabic translations
 */
console.log('[I18n] Script loading...');

const I18n = (function() {
    'use strict';

    // Translation dictionaries - will be merged with AppTranslations from translations.js
    let translations = {
        en: {
            // Navigation
            'nav.dashboard': 'Dashboard',
            'nav.accidents': 'Accidents',
            'nav.browseAccidents': 'Browse accidents',
            'nav.browseAccidentsDesc': 'Search, filter, and view details',
            'nav.reportAccident': 'Report an accident',
            'nav.reportAccidentDesc': 'Submit a new report',
            'nav.myReports': 'My reports',
            'nav.myReportsDesc': 'Track your submitted reports',
            'nav.administration': 'Administration',
            'nav.importCSV': 'Import CSV',
            'nav.importCSVDesc': 'Upload accident batches',
            'nav.usersManagement': 'Users management',
            'nav.usersManagementDesc': 'Manage accounts and access',
            'nav.reports': 'Reports',
            'nav.reportsDesc': 'Review and audit reports',
            'nav.statistics': 'Statistics',
            'nav.summary': 'Summary',
            'nav.summaryDesc': 'KPIs and key metrics',
            'nav.visuals': 'Visuals',
            'nav.visualsDesc': 'Charts and trends',
            'nav.map': 'Map',
            'nav.mapDesc': 'Explore regions interactively',
            'nav.predictions': 'Predictions',
            'nav.predictionsDesc': 'AI-powered risk forecasting',
            
            // Account menu
            'nav.account': 'Account',
            'nav.accountSettings': 'Account settings',
            'nav.accountSettingsDesc': 'Update your info and preferences',
            'nav.darkMode': 'Dark mode',
            'nav.lightMode': 'Light mode',
            'nav.signOut': 'Sign out',
            'nav.logout': 'Logout',
            'nav.logoutDesc': 'Sign out of your session',
            'nav.services': 'Services',
            
            // Language
            'nav.language': 'Language',
            'lang.english': 'English',
            'lang.french': 'Français',
            'lang.arabic': 'العربية',
            
            // Common
            'common.search': 'Search',
            'common.filter': 'Filter',
            'common.save': 'Save',
            'common.cancel': 'Cancel',
            'common.delete': 'Delete',
            'common.edit': 'Edit',
            'common.view': 'View',
            'common.loading': 'Loading...',
            'common.noResults': 'No results found',
            'common.error': 'An error occurred',
            'common.success': 'Success',
            'common.confirm': 'Confirm',
            'common.close': 'Close',
            'common.next': 'Next',
            'common.previous': 'Previous',
            'common.submit': 'Submit',
            'common.reset': 'Reset',
            
            // Dashboard
            'dashboard.title': 'Dashboard',
            'dashboard.welcome': 'Welcome back',
            'dashboard.recentAccidents': 'Recent Accidents',
            'dashboard.quickStats': 'Quick Stats',
            'dashboard.weather': 'Weather Advisory',
            'dashboard.riskAssessment': 'Risk Assessment',
            
            // Statistics
            'stats.title': 'Statistics',
            'stats.totalAccidents': 'Total Accidents',
            'stats.fatalities': 'Fatalities',
            'stats.injuries': 'Injuries',
            'stats.avgSeverity': 'Average Severity',
        },
        
        fr: {
            // Navigation
            'nav.dashboard': 'Tableau de bord',
            'nav.accidents': 'Accidents',
            'nav.browseAccidents': 'Parcourir les accidents',
            'nav.browseAccidentsDesc': 'Rechercher, filtrer et voir les détails',
            'nav.reportAccident': 'Signaler un accident',
            'nav.reportAccidentDesc': 'Soumettre un nouveau rapport',
            'nav.myReports': 'Mes rapports',
            'nav.myReportsDesc': 'Suivre vos rapports soumis',
            'nav.administration': 'Administration',
            'nav.importCSV': 'Importer CSV',
            'nav.importCSVDesc': 'Télécharger des lots d\'accidents',
            'nav.usersManagement': 'Gestion des utilisateurs',
            'nav.usersManagementDesc': 'Gérer les comptes et les accès',
            'nav.reports': 'Rapports',
            'nav.reportsDesc': 'Examiner et auditer les rapports',
            'nav.statistics': 'Statistiques',
            'nav.summary': 'Résumé',
            'nav.summaryDesc': 'KPIs et métriques clés',
            'nav.visuals': 'Visuels',
            'nav.visualsDesc': 'Graphiques et tendances',
            'nav.map': 'Carte',
            'nav.mapDesc': 'Explorer les régions de manière interactive',
            'nav.predictions': 'Prédictions',
            'nav.predictionsDesc': 'Prévisions de risques par IA',
            
            // Account menu
            'nav.account': 'Compte',
            'nav.accountSettings': 'Paramètres du compte',
            'nav.accountSettingsDesc': 'Mettre à jour vos infos et préférences',
            'nav.darkMode': 'Mode sombre',
            'nav.lightMode': 'Mode clair',
            'nav.signOut': 'Déconnexion',
            'nav.logout': 'Déconnexion',
            'nav.logoutDesc': 'Se déconnecter de votre session',
            'nav.services': 'Services',
            
            // Language
            'nav.language': 'Langue',
            'lang.english': 'English',
            'lang.french': 'Français',
            'lang.arabic': 'العربية',
            
            // Common
            'common.search': 'Rechercher',
            'common.filter': 'Filtrer',
            'common.save': 'Enregistrer',
            'common.cancel': 'Annuler',
            'common.delete': 'Supprimer',
            'common.edit': 'Modifier',
            'common.view': 'Voir',
            'common.loading': 'Chargement...',
            'common.noResults': 'Aucun résultat trouvé',
            'common.error': 'Une erreur s\'est produite',
            'common.success': 'Succès',
            'common.confirm': 'Confirmer',
            'common.close': 'Fermer',
            'common.next': 'Suivant',
            'common.previous': 'Précédent',
            'common.submit': 'Soumettre',
            'common.reset': 'Réinitialiser',
            
            // Dashboard
            'dashboard.title': 'Tableau de bord',
            'dashboard.welcome': 'Bienvenue',
            'dashboard.recentAccidents': 'Accidents récents',
            'dashboard.quickStats': 'Statistiques rapides',
            'dashboard.weather': 'Avis météo',
            'dashboard.riskAssessment': 'Évaluation des risques',
            
            // Statistics
            'stats.title': 'Statistiques',
            'stats.totalAccidents': 'Total des accidents',
            'stats.fatalities': 'Décès',
            'stats.injuries': 'Blessures',
            'stats.avgSeverity': 'Gravité moyenne',
        },
        
        ar: {
            // Navigation
            'nav.dashboard': 'لوحة التحكم',
            'nav.accidents': 'الحوادث',
            'nav.browseAccidents': 'تصفح الحوادث',
            'nav.browseAccidentsDesc': 'البحث والتصفية وعرض التفاصيل',
            'nav.reportAccident': 'الإبلاغ عن حادث',
            'nav.reportAccidentDesc': 'تقديم تقرير جديد',
            'nav.myReports': 'تقاريري',
            'nav.myReportsDesc': 'تتبع التقارير المقدمة',
            'nav.administration': 'الإدارة',
            'nav.importCSV': 'استيراد CSV',
            'nav.importCSVDesc': 'تحميل دفعات الحوادث',
            'nav.usersManagement': 'إدارة المستخدمين',
            'nav.usersManagementDesc': 'إدارة الحسابات والوصول',
            'nav.reports': 'التقارير',
            'nav.reportsDesc': 'مراجعة وتدقيق التقارير',
            'nav.statistics': 'الإحصائيات',
            'nav.summary': 'الملخص',
            'nav.summaryDesc': 'مؤشرات الأداء والمقاييس',
            'nav.visuals': 'الرسوم البيانية',
            'nav.visualsDesc': 'الرسوم والاتجاهات',
            'nav.map': 'الخريطة',
            'nav.mapDesc': 'استكشاف المناطق تفاعلياً',
            'nav.predictions': 'التنبؤات',
            'nav.predictionsDesc': 'توقعات المخاطر بالذكاء الاصطناعي',
            
            // Account menu
            'nav.account': 'الحساب',
            'nav.accountSettings': 'إعدادات الحساب',
            'nav.accountSettingsDesc': 'تحديث معلوماتك وتفضيلاتك',
            'nav.darkMode': 'الوضع الداكن',
            'nav.lightMode': 'الوضع الفاتح',
            'nav.signOut': 'تسجيل الخروج',
            'nav.logout': 'تسجيل الخروج',
            'nav.logoutDesc': 'الخروج من جلستك',
            'nav.services': 'الخدمات',
            
            // Language
            'nav.language': 'اللغة',
            'lang.english': 'English',
            'lang.french': 'Français',
            'lang.arabic': 'العربية',
            
            // Common
            'common.search': 'بحث',
            'common.filter': 'تصفية',
            'common.save': 'حفظ',
            'common.cancel': 'إلغاء',
            'common.delete': 'حذف',
            'common.edit': 'تعديل',
            'common.view': 'عرض',
            'common.loading': 'جاري التحميل...',
            'common.noResults': 'لم يتم العثور على نتائج',
            'common.error': 'حدث خطأ',
            'common.success': 'نجاح',
            'common.confirm': 'تأكيد',
            'common.close': 'إغلاق',
            'common.next': 'التالي',
            'common.previous': 'السابق',
            'common.submit': 'إرسال',
            'common.reset': 'إعادة تعيين',
            
            // Dashboard
            'dashboard.title': 'لوحة التحكم',
            'dashboard.welcome': 'مرحباً بك',
            'dashboard.recentAccidents': 'الحوادث الأخيرة',
            'dashboard.quickStats': 'إحصائيات سريعة',
            'dashboard.weather': 'تنبيه الطقس',
            'dashboard.riskAssessment': 'تقييم المخاطر',
            
            // Statistics
            'stats.title': 'الإحصائيات',
            'stats.totalAccidents': 'إجمالي الحوادث',
            'stats.fatalities': 'الوفيات',
            'stats.injuries': 'الإصابات',
            'stats.avgSeverity': 'متوسط الخطورة',
        }
    };

    // Language metadata with SVG flags
    const languages = {
        en: { 
            name: 'English', 
            dir: 'ltr',
            flagSvg: '<svg viewBox="0 0 640 480" class="flag-icon"><path fill="#012169" d="M0 0h640v480H0z"/><path fill="#FFF" d="m75 0 244 181L562 0h78v62L400 241l240 178v61h-80L320 301 81 480H0v-60l239-178L0 64V0h75z"/><path fill="#C8102E" d="m424 281 216 159v40L369 281h55zm-184 20 6 35L54 480H0l240-179zM640 0v3L391 191l2-44L590 0h50zM0 0l239 176h-60L0 42V0z"/><path fill="#FFF" d="M241 0v480h160V0H241zM0 160v160h640V160H0z"/><path fill="#C8102E" d="M0 193v96h640v-96H0zM273 0v480h96V0h-96z"/></svg>'
        },
        fr: { 
            name: 'Français', 
            dir: 'ltr',
            flagSvg: '<svg viewBox="0 0 640 480" class="flag-icon"><path fill="#002654" d="M0 0h213.3v480H0z"/><path fill="#FFF" d="M213.3 0h213.4v480H213.3z"/><path fill="#CE1126" d="M426.7 0H640v480H426.7z"/></svg>'
        },
        ar: { 
            name: 'العربية', 
            dir: 'rtl',
            flagSvg: '<svg viewBox="0 0 640 480" class="flag-icon"><path fill="#E70013" d="M0 0h640v480H0z"/><circle cx="320" cy="240" r="96" fill="#FFF"/><circle cx="340" cy="240" r="80" fill="#E70013"/><path fill="#FFF" d="m260 240 60-20 12 37-48-35h48l-48 35 12-37z"/></svg>'
        }
    };

    let currentLang = 'en';

    /**
     * Initialize the i18n system
     */
    function init() {
        // Merge AppTranslations from translations.js if available
        if (window.AppTranslations) {
            Object.keys(window.AppTranslations).forEach(lang => {
                if (translations[lang]) {
                    translations[lang] = Object.assign({}, translations[lang], window.AppTranslations[lang]);
                } else {
                    translations[lang] = window.AppTranslations[lang];
                }
            });
        }
        
        // Load saved language from localStorage
        const savedLang = localStorage.getItem('app-language');
        if (savedLang && translations[savedLang]) {
            currentLang = savedLang;
        }
        
        // Apply initial language
        applyLanguage(currentLang);
        
        // Setup language switcher
        setupLangSwitcher();
    }
    
    /**
     * Setup the language switcher dropdown
     */
    function setupLangSwitcher() {
        const switcher = document.querySelector('.lang-switcher');
        const trigger = document.getElementById('langSwitcherBtn');
        const dropdown = document.getElementById('langDropdown');
        
        if (!switcher || !trigger || !dropdown) return;
        
        // Toggle dropdown on trigger click
        trigger.addEventListener('click', function(e) {
            e.stopPropagation();
            switcher.classList.toggle('is-open');
        });
        
        // Handle language option clicks
        const options = dropdown.querySelectorAll('.lang-switcher__option');
        options.forEach(function(option) {
            option.addEventListener('click', function(e) {
                e.stopPropagation();
                const lang = this.getAttribute('data-lang');
                if (lang) {
                    setLanguage(lang);
                    switcher.classList.remove('is-open');
                }
            });
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!switcher.contains(e.target)) {
                switcher.classList.remove('is-open');
            }
        });
        
        // Close on Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                switcher.classList.remove('is-open');
            }
        });
    }

    /**
     * Get translation for a key
     */
    function t(key, fallback = null) {
        const dict = translations[currentLang];
        if (dict && dict[key]) {
            return dict[key];
        }
        // Fallback to English
        if (translations.en && translations.en[key]) {
            return translations.en[key];
        }
        return fallback || key;
    }

    /**
     * Set the current language
     */
    function setLanguage(lang) {
        console.log('[I18n] setLanguage called with:', lang);
        if (!translations[lang]) {
            console.warn(`Language "${lang}" not supported`);
            return false;
        }
        
        currentLang = lang;
        localStorage.setItem('app-language', lang);
        console.log('[I18n] Calling applyLanguage...');
        applyLanguage(lang);
        
        // Dispatch event for other components to listen
        document.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
        
        console.log('[I18n] Language changed to:', lang);
        return true;
    }

    /**
     * Get current language
     */
    function getLanguage() {
        return currentLang;
    }

    /**
     * Apply language to all elements with data-i18n attribute
     */
    function applyLanguage(lang) {
        const elements = document.querySelectorAll('[data-i18n]');
        console.log('[I18n] applyLanguage - found', elements.length, 'elements with data-i18n');
        
        elements.forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translation = t(key);
            console.log('[I18n] Translating:', key, '->', translation);
            
            // Check if it's a placeholder or title attribute
            if (el.hasAttribute('data-i18n-attr')) {
                const attr = el.getAttribute('data-i18n-attr');
                el.setAttribute(attr, translation);
            } else {
                el.textContent = translation;
            }
        });

        // Update document direction for RTL languages
        const langInfo = languages[lang];
        document.documentElement.dir = langInfo.dir;
        document.documentElement.lang = lang;
        
        // Add/remove RTL class for additional styling
        if (langInfo.dir === 'rtl') {
            document.body.classList.add('rtl');
        } else {
            document.body.classList.remove('rtl');
        }

        // Update language switcher UI
        updateLanguageSwitcherUI(lang);
    }

    /**
     * Update the language switcher UI elements
     */
    function updateLanguageSwitcherUI(lang) {
        const langInfo = languages[lang];
        
        // Update current language display with SVG flag
        const flagEl = document.getElementById('currentLangFlag');
        const codeEl = document.getElementById('currentLangCode');
        
        if (flagEl && langInfo.flagSvg) {
            flagEl.innerHTML = langInfo.flagSvg;
        }
        if (codeEl) codeEl.textContent = lang.toUpperCase();

        // Update checkmarks and active state in dropdown
        document.querySelectorAll('.lang-switcher__option').forEach(option => {
            const optionLang = option.getAttribute('data-lang');
            
            if (optionLang === lang) {
                option.classList.add('lang-switcher__option--active');
            } else {
                option.classList.remove('lang-switcher__option--active');
            }
        });
    }

    /**
     * Add translation to a specific language
     */
    function addTranslation(lang, key, value) {
        if (!translations[lang]) {
            translations[lang] = {};
        }
        translations[lang][key] = value;
    }

    /**
     * Add multiple translations at once
     */
    function addTranslations(lang, dict) {
        if (!translations[lang]) {
            translations[lang] = {};
        }
        Object.assign(translations[lang], dict);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Public API
    return {
        t,
        setLanguage,
        getLanguage,
        addTranslation,
        addTranslations,
        applyLanguage,
        languages
    };
})();

// Make I18n available globally
window.I18n = I18n;
console.log('[I18n] window.I18n is now available:', !!window.I18n);
