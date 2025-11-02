/**
 * Translation Key Validation Script
 * Feature: 005-mini-app-improvements
 *
 * Validates that all translation keys are present in all languages
 * Works with i18n/index.ts structure
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
 * Parse translations from index.ts file
 */
function parseTranslationsFromFile() {
  const indexPath = join(__dirname, 'index.ts');
  const content = readFileSync(indexPath, 'utf-8');

  // Extract the resources object
  const resourcesMatch = content.match(/const resources = \{([\s\S]+?)\};/);
  if (!resourcesMatch) {
    console.error('❌ Could not find resources object in index.ts');
    process.exit(1);
  }

  // Extract EN translation block
  const enMatch = content.match(/en: \{\s*translation: \{([\s\S]+?)\n    \},\s*\},/);
  if (!enMatch) {
    console.error('❌ Could not find EN translation block');
    process.exit(1);
  }

  // Extract RU translation block
  const ruMatch = content.match(/ru: \{\s*translation: \{([\s\S]+?)\n    \},\s*\},/);
  if (!ruMatch) {
    console.error('❌ Could not find RU translation block');
    process.exit(1);
  }

  try {
    // Build executable JavaScript to parse the objects
    const enCode = `const translation = {${enMatch[1]}}; translation;`;
    const ruCode = `const translation = {${ruMatch[1]}}; translation;`;

    const enTranslation = eval(enCode);
    const ruTranslation = eval(ruCode);

    return { en: enTranslation, ru: ruTranslation };
  } catch (e) {
    console.error('❌ Failed to parse translation objects:', e.message);
    process.exit(1);
  }
}

/**
 * Main validation
 */
function validateTranslations() {
  console.log('\n🔍 Validating translation keys...\n');

  const { en, ru } = parseTranslationsFromFile();

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
