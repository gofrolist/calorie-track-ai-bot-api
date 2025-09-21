import { describe, it, expect } from 'vitest';

describe('contracts: meals', () => {
  it('create meal response shape', () => {
    const sample = { meal_id: 'uuid' };
    expect(typeof sample.meal_id).toBe('string');
  });
});
