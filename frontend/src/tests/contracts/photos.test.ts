import { describe, it, expect } from 'vitest';

describe('contracts: photos', () => {
  it('presign response shape', () => {
    const sample = { photo_id: 'uuid', upload_url: 'https://example.com' };
    expect(typeof sample.photo_id).toBe('string');
    expect(typeof sample.upload_url).toBe('string');
  });
});
