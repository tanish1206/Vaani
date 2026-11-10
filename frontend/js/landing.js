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
      finalCtaTitle: "Your business. Your voice. Your Vaani.",
      finalCtaTagline: "Apne roz ke kaam ko aur aasaan banaiye. Boliye, Vaani sambhal legi.",
      finalCtaBtn: "Start Speaking"
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
      finalCtaTitle: "आपका व्यापार। आपकी आवाज़। आपकी वाणी।",
      finalCtaTagline: "अपने रोज़ के काम को और आसान बनाइए। बोलिए, वाणी संभाल लेगी।",
      finalCtaBtn: "बोलना शुरू करें"
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
      finalCtaTitle: "तुमचा व्यवसाय. तुमचा आवाज. तुमची वाणी.",
      finalCtaTagline: "आपली रोजची कामे सोपी करा. बोला, वाणी सांभाळून घेईल.",
      finalCtaBtn: "बोलायला सुरुवात करा"
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
          const toggleItem = () => {
            const isOpen = item.classList.contains('open');
            faqItems.forEach((f) => {
              f.classList.remove('open');
              const btn = f.querySelector('.faq-question-btn');
              if (btn) btn.setAttribute('aria-expanded', 'false');
            });
            if (!isOpen) {
              item.classList.add('open');
              questionBtn.setAttribute('aria-expanded', 'true');
            }
          };

          questionBtn.addEventListener('click', toggleItem);
          questionBtn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleItem();
            }
          });
        }
      });
    }

    initLanguageTabs() {
      const langTabs = document.querySelectorAll('.lang-tab-pill');
      const langData = {
        hi: {
          cmd: '"रमेश को दो सौ उधार लिख दो और सुनीता ने डेढ़ सौ दिए।"',
          cmdTrans: 'Action: Credit ₹200 to Ramesh, Record payment of ₹150 from Sunita.',
          resp: '"रमेश के खाते में ₹200 जोड़ दिए, अब बाकी ₹850 है। सुनीता के ₹150 जमा हो गए।"',
          respTrans: 'Audio confirmation delivered back in native natural speech.'
        },
        mr: {
          cmd: '"रमेश ला दोनशे उधार लिहा आणि सुनीताने दीडशे दिले."',
          cmdTrans: 'Action: Credit ₹200 to Ramesh, Record payment of ₹150 from Sunita.',
          resp: '"रमेश यांच्या खात्यात ₹200 उधार नोंदवले. आता बाकी ₹850 आहे. सुनीताचे ₹150 जमा झाले."',
          respTrans: 'Marathi Timbre v2.5 voice confirmation.'
        },
        en: {
          cmd: '"Ramesh ko 200 udhaar likh de aur Sunita ne 150 diye"',
          cmdTrans: 'Code-mixed Hinglish natural shop command.',
          resp: '"Ramesh ke khaate mein ₹200 jod diye (ab baaki ₹850). Sunita ke ₹150 jama ho gaye."',
          respTrans: 'Code-mixed speech output with confirmed numbers.'
        }
      };

      langTabs.forEach((tab) => {
        tab.addEventListener('click', () => {
          langTabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          const targetLang = tab.getAttribute('data-lang');
          if (targetLang && langData[targetLang]) {
            const data = langData[targetLang];
            const cmdEl = document.getElementById('langQuoteCmd');
            const cmdTransEl = document.getElementById('langQuoteCmdTrans');
            const respEl = document.getElementById('langQuoteResp');
            const respTransEl = document.getElementById('langQuoteRespTrans');
            if (cmdEl) cmdEl.textContent = data.cmd;
            if (cmdTransEl) cmdTransEl.textContent = data.cmdTrans;
            if (respEl) respEl.textContent = data.resp;
            if (respTransEl) respTransEl.textContent = data.respTrans;
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
        '.showcase-stage .mockup-card-khata, .showcase-stage .mockup-card-parchi, .showcase-stage .mockup-card-sensex, .showcase-stage .mockup-phone-frame, #voice-lab, #modules, #trust-safety, #how-it-works, #faq, .final-cta-section, .languages-tab-wrapper, .pipeline-diagram, .modules-grid, .trust-grid'
      );

      targets.forEach((el) => {
        el.classList.add('reveal-on-scroll');
        if (
          el.classList.contains('modules-grid') ||
          el.classList.contains('pipeline-diagram') ||
          el.classList.contains('trust-grid')
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

