/**
 * Translation Key Validation Script
 * Feature: 005-mini-app-improvements
 *
 * Validates that all translation keys are present in all languages
 * and that no keys are missing between English and Russian translations.
 *
 * Usage:
 *   npm run i18n:validate
 */

import i18n from './index.js';

interface TranslationObject {
  [key: string]: string | TranslationObject;
}

/**
 * Recursively flatten nested translation object into dot-notation keys
 */
function flattenKeys(obj: TranslationObject, prefix = ''): string[] {
  return Object.keys(obj).reduce((acc: string[], key: string) => {
    const newPrefix = prefix ? `${prefix}.${key}` : key;
    const value = obj[key];

    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      return [...acc, ...flattenKeys(value, newPrefix)];
    }
    return [...acc, newPrefix];
  }, []);
}

/**
 * Main validation logic
 */
function validateTranslations(): void {
  console.log('\n🔍 Validating translation keys...\n');

  // Get translations from i18n instance
  const enTranslation = i18n.getResourceBundle('en', 'translation') as TranslationObject;
  const ruTranslation = i18n.getResourceBundle('ru', 'translation') as TranslationObject;

  if (!enTranslation || !ruTranslation) {
    console.error('❌ Failed to load translation resources');
    process.exit(1);
  }

  // Flatten keys
  const enKeys = new Set(flattenKeys(enTranslation));
  const ruKeys = new Set(flattenKeys(ruTranslation));

  console.log(`  📄 en: ${enKeys.size} keys loaded`);
  console.log(`  📄 ru: ${ruKeys.size} keys loaded`);
  console.log('');

  let hasErrors = false;

  // Find keys missing in ru
  const missingInRu = Array.from(enKeys).filter(k => !ruKeys.has(k));
  if (missingInRu.length > 0) {
    hasErrors = true;
    console.error('❌ Missing in ru (present in en):');
    missingInRu.forEach(key => console.error(`   - ${key}`));
    console.error('');
  }

  // Find keys missing in en
  const missingInEn = Array.from(ruKeys).filter(k => !enKeys.has(k));
  if (missingInEn.length > 0) {
    hasErrors = true;
    console.error('❌ Missing in en (present in ru):');
    missingInEn.forEach(key => console.error(`   - ${key}`));
    console.error('');
  }

  // Check for empty values (optional warning, not fatal)
  const checkEmptyValues = (obj: TranslationObject, prefix = '', lang: string): string[] => {
    const emptyKeys: string[] = [];

    for (const [key, value] of Object.entries(obj)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;

      if (typeof value === 'string' && value.trim() === '') {
        emptyKeys.push(fullKey);
      } else if (typeof value === 'object' && value !== null) {
        emptyKeys.push(...checkEmptyValues(value, fullKey, lang));
      }
    }

    return emptyKeys;
  };

  const enEmpty = checkEmptyValues(enTranslation, '', 'en');
  const ruEmpty = checkEmptyValues(ruTranslation, '', 'ru');

  if (enEmpty.length > 0) {
    console.warn(`⚠️  Warning: en has ${enEmpty.length} empty values:`);
    enEmpty.forEach(key => console.warn(`   - ${key}`));
    console.warn('');
  }

  if (ruEmpty.length > 0) {
    console.warn(`⚠️  Warning: ru has ${ruEmpty.length} empty values:`);
    ruEmpty.forEach(key => console.warn(`   - ${key}`));
    console.warn('');
  }

  // Final result
  if (hasErrors) {
    console.error('❌ Translation validation FAILED\n');
    console.error('Please add missing keys to maintain consistency.\n');
    process.exit(1);
  } else {
    console.log('✅ All translation keys validated successfully!\n');
    console.log(`   Total keys: ${enKeys.size}`);
    console.log(`   Languages: en, ru`);
    console.log('');
    process.exit(0);
  }
}

// Run validation
validateTranslations();
