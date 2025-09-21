import { describe, it, expect } from 'vitest';
import i18n from '../i18n';

describe('i18n', () => {
  it('loads English by default', () => {
    expect(i18n.language).toBe('en');
    expect(i18n.t('today.title')).toBe('Today');
  });

  it('can switch to Russian', async () => {
    await i18n.changeLanguage('ru');
    expect(i18n.language).toBe('ru');
    expect(i18n.t('today.title')).toBe('Сегодня');
  });
});
