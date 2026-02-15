/**
 * Translation Key Validation Script
 * Feature: 005-mini-app-improvements
 *
 * Validates that all translation keys are present in all languages
 * Works with i18n/en.ts and i18n/ru.ts structure
 *
 * Usage: npm run i18n:validate
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Recursively flatten nested object into dot-notation keys
 */
function flattenKeys(obj, prefix = '') {
  return Object.keys(obj).reduce((acc, key) => {
    const newPrefix = prefix ? `${prefix}.${key}` : key;
    const value = obj[key];

    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      return [...acc, ...flattenKeys(value, newPrefix)];
    }
    return [...acc, newPrefix];
  }, []);
}

/**
 * Parse a translation object from a .ts file
 * Expects: const <name> = { ... } as const; export default <name>;
 */
function parseTranslationFile(filePath) {
  const content = readFileSync(filePath, 'utf-8');

  // Remove TypeScript syntax to get a plain JS object literal
  const cleaned = content
    .replace(/^const \w+ = /, '')
    .replace(/export default \w+;\s*/g, '')
    .replace(/\} as const;/, '}')
    .trim();

  try {
    // Note: eval is used here intentionally to parse TypeScript object literals
    // from our own project files in a dev-only validation script.
    const translation = eval(`(${cleaned})`);
    return translation;
  } catch (e) {
    console.error(`❌ Failed to parse ${filePath}:`, e.message);
    process.exit(1);
  }
}

/**
 * Parse translations from separate en.ts and ru.ts files
 */
function parseTranslationsFromFiles() {
  const enPath = join(__dirname, 'en.ts');
  const ruPath = join(__dirname, 'ru.ts');

  const enTranslation = parseTranslationFile(enPath);
  const ruTranslation = parseTranslationFile(ruPath);

  return { en: enTranslation, ru: ruTranslation };
}

/**
 * Main validation
 */
function validateTranslations() {
  console.log('\n🔍 Validating translation keys...\n');

  const { en, ru } = parseTranslationsFromFiles();

  const enKeys = new Set(flattenKeys(en));
  const ruKeys = new Set(flattenKeys(ru));

  console.log(`  📄 en: ${enKeys.size} keys loaded`);
  console.log(`  📄 ru: ${ruKeys.size} keys loaded`);
  console.log('');

  let hasErrors = false;

  // Find missing keys
  const missingInRu = Array.from(enKeys).filter(k => !ruKeys.has(k));
  if (missingInRu.length > 0) {
    hasErrors = true;
    console.error('❌ Missing in ru (present in en):');
    missingInRu.forEach(key => console.error(`   - ${key}`));
    console.error('');
  }

  const missingInEn = Array.from(ruKeys).filter(k => !enKeys.has(k));
  if (missingInEn.length > 0) {
    hasErrors = true;
    console.error('❌ Missing in en (present in ru):');
    missingInEn.forEach(key => console.error(`   - ${key}`));
    console.error('');
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
