import { describe, it, expect } from 'vitest';

describe('contracts: estimates', () => {
  it('estimate response shape', () => {
    const sample = {
      id: 'uuid',
      photo_id: 'uuid',
      kcal_mean: 100,
      kcal_min: 90,
      kcal_max: 110,
      confidence: 0.9,
      breakdown: [{ label: 'apple', kcal: 52, confidence: 0.8 }],
      status: 'done',
    };
    expect(typeof sample.id).toBe('string');
    expect(Array.isArray(sample.breakdown)).toBe(true);
  });
});
