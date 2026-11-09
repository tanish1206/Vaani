/**
 * VAANI — Landing Page Controller
 * Handles Navigation, Language Localization (EN / HI / MR),
 * Night Mode, FAQ Accordion, and Interactive Product Showcases
 */

(function () {
  'use strict';

  // Localization Dictionary
  const I18N_STRINGS = {
    en: {
      brandTagline: "Boliye. Vaani Sambhal Legi.",
      navHome: "Home",
      navKhata: "Bol-Khata",
      navParchi: "Parchi",
      navBazaar: "Sensex Awaaz",
      navSettings: "Settings",
      heroHeadlineBoliye: "Boliye.",
      heroHeadlineVaani: "Vaani",
      heroCopy: "Apne kaam, hisaab aur zaroori jaankari — ab sirf apni awaaz se.",
      startSpeaking: "Start Speaking",
      watchDemo: "Watch Demo",
      finalCtaTitle: "Boliye. Vaani Sambhal Legi.",
      finalCtaTagline: "Voice-first intelligence crafted for Indian enterprise, local kiranas, and families.",
      finalCtaBtn: "Experience Vaani Now"
    },
    hi: {
      brandTagline: "बोलिए। वाणी संभाल लेगी।",
      navHome: "होम",
      navKhata: "बोल-खाता",
      navParchi: "पर्ची",
      navBazaar: "सेंसेक्स आवाज़",
      navSettings: "सेटिंग्स",
      heroHeadlineBoliye: "बोलिए।",
      heroHeadlineVaani: "वाणी",
      heroCopy: "अपने काम, हिसाब और ज़रूरी जानकारी — अब सिर्फ़ अपनी आवाज़ से।",
      startSpeaking: "बोलना शुरू करें",
      watchDemo: "डेमो देखें",
      finalCtaTitle: "बोलिए। वाणी संभाल लेगी।",
      finalCtaTagline: "भारतीय दुकानों, छोटे व्यापारियों और परिवारों के लिए आवाज़ पर चलने वाला एआई सहायक।",
      finalCtaBtn: "वाणी का अनुभव लें"
    },
    mr: {
      brandTagline: "बोला. वाणी सांभाळून घेईल.",
      navHome: "मुख्यपृष्ठ",
      navKhata: "बोल-खाते",
      navParchi: "चिट्ठी (पर्ची)",
      navBazaar: "सेन्सेक्स आवाज",
      navSettings: "सेटिंग्ज",
      heroHeadlineBoliye: "बोला.",
      heroHeadlineVaani: "वाणी",
      heroCopy: "आपली कामे, हिशोब आणि महत्त्वाची माहिती — आता फक्त आपल्या आवाजाने.",
      startSpeaking: "बोलायला सुरुवात करा",
      watchDemo: "डेमो पाहा",
      finalCtaTitle: "बोला. वाणी सांभाळून घेईल.",
      finalCtaTagline: "महाराष्ट्रातील व्यापारी, किराणा दुकाने आणि कुटुंबांसाठी अस्सल मराठी व कोड-मिक्स्ड व्हॉइस एआय.",
      finalCtaBtn: "वाणी सुरू करा"
    }
  };

  class LandingController {
    constructor() {
      this.currentLang = 'en';
      this.initTheme();
      this.initLocalization();
      this.initFaqAccordion();
      this.initLanguageTabs();
      this.initHeaderScroll();
      this.initVisualizer();
      this.initScrollReveals();
    }

    initTheme() {
      const themeToggleBtn = document.getElementById('themeToggleBtn');
      if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
          const currentTheme = document.documentElement.getAttribute('data-theme');
          const nextTheme = currentTheme === 'night' ? 'light' : 'night';
          document.documentElement.setAttribute('data-theme', nextTheme);
          localStorage.setItem('vaani-theme', nextTheme);
        });
      }

      const savedTheme = localStorage.getItem('vaani-theme');
      if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
      }
    }

    initLocalization() {
      const langSelectorBtn = document.getElementById('langSelectorBtn');
      const langText = document.getElementById('currentLangLabel');

      if (langSelectorBtn) {
        langSelectorBtn.addEventListener('click', () => {
          const langs = ['en', 'hi', 'mr'];
          const nextIdx = (langs.indexOf(this.currentLang) + 1) % langs.length;
          this.switchLanguage(langs[nextIdx]);
        });
      }
    }

    switchLanguage(lang) {
      this.currentLang = lang;
      const dict = I18N_STRINGS[lang] || I18N_STRINGS.en;
      
      const langLabel = document.getElementById('currentLangLabel');
      if (langLabel) {
        langLabel.textContent = lang === 'en' ? 'EN' : (lang === 'hi' ? 'हिन्दी' : 'मराठी');
      }

      // Update text in DOM elements
      this.updateText('heroHeadlineBoliye', dict.heroHeadlineBoliye);
      this.updateText('heroHeadlineVaani', dict.heroHeadlineVaani);
      this.updateText('heroSupportingCopy', dict.heroCopy);
      this.updateText('heroVoiceBtnText', dict.startSpeaking);
      this.updateText('heroWatchDemoText', dict.watchDemo);
      this.updateText('finalCtaTitle', dict.finalCtaTitle);
      this.updateText('finalCtaTagline', dict.finalCtaTagline);
      this.updateText('finalCtaBtnText', dict.finalCtaBtn);

      // Set HTML lang attribute
      document.documentElement.setAttribute('lang', lang);
    }

    updateText(id, text) {
      const el = document.getElementById(id);
      if (el) el.textContent = text;
    }

    initFaqAccordion() {
      const faqItems = document.querySelectorAll('.faq-item');
      faqItems.forEach((item) => {
        const questionBtn = item.querySelector('.faq-question-btn');
        if (questionBtn) {
          questionBtn.addEventListener('click', () => {
            const isOpen = item.classList.contains('open');
            // Close others for clean accordion
            faqItems.forEach((f) => f.classList.remove('open'));
            if (!isOpen) {
              item.classList.add('open');
            }
          });
        }
      });
    }

    initLanguageTabs() {
      const langTabs = document.querySelectorAll('.lang-tab-pill');
      langTabs.forEach((tab) => {
        tab.addEventListener('click', () => {
          langTabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          const targetLang = tab.getAttribute('data-lang');
          if (targetLang) {
            this.switchLanguage(targetLang);
          }
        });
      });
    }

    initHeaderScroll() {
      const header = document.querySelector('.site-header');
      window.addEventListener('scroll', () => {
        if (window.scrollY > 40) {
          header.classList.add('scrolled');
        } else {
          header.classList.remove('scrolled');
        }
      });
    }

    initVisualizer() {
      if (window.AudioWaveformVisualizer) {
        window.vaaniVisualizer = new window.AudioWaveformVisualizer('heroAudioCanvas');
      }
    }

    initScrollReveals() {
      const targets = document.querySelectorAll(
        '.showcase-stage .mockup-card-khata, .showcase-stage .mockup-card-parchi, .showcase-stage .mockup-card-sensex, .showcase-stage .mockup-phone-frame, #voice-lab, #modules, #how-it-works, #faq, .final-cta-section, .languages-tab-wrapper, .pipeline-diagram, .modules-grid'
      );

      targets.forEach((el) => {
        el.classList.add('reveal-on-scroll');
        if (
          el.classList.contains('modules-grid') ||
          el.classList.contains('pipeline-diagram')
        ) {
          el.classList.add('stagger-children');
        }
      });

      if (!('IntersectionObserver' in window)) {
        targets.forEach((el) => el.classList.add('is-inview'));
        return;
      }

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-inview');
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.18, rootMargin: '0px 0px -8% 0px' }
      );

      targets.forEach((el) => observer.observe(el));
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    window.vaaniLanding = new LandingController();
  });
})();

