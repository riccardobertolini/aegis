import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import en from './locales/en.json'
import it from './locales/it.json'
import de from './locales/de.json'
import fr from './locales/fr.json'

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en }, it: { translation: it }, de: { translation: de }, fr: { translation: fr } },
    fallbackLng: 'en',
    supportedLngs: ['en', 'it', 'de', 'fr'],
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'aegis_lang',
    },
    interpolation: { escapeValue: false },
  })

export default i18n
