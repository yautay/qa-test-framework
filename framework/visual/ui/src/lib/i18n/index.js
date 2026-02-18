import { ref, computed } from "vue";
import en from "./locales/en.json";
import pl from "./locales/pl.json";

const STORAGE_KEY = "visual-report-locale";

const messages = { en, pl };

const savedLocale =
  typeof window !== "undefined"
    ? window.localStorage.getItem(STORAGE_KEY)
    : null;

const locale = ref(savedLocale || "en");

export function setLocale(lang) {
  if (messages[lang]) {
    locale.value = lang;
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, lang);
    }
  }
}

export function t(key) {
  const keys = key.split(".");
  let value = messages[locale.value];
  for (const k of keys) {
    if (value && typeof value === "object") {
      value = value[k];
    } else {
      return key;
    }
  }
  return value ?? key;
}

export { locale };
