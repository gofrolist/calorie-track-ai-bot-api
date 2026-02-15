import { describe, it, expect, vi, beforeEach } from 'vitest';
import { customFetch, ApiError } from '../client';

describe('customFetch', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('adds x-user-id header from Telegram', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );

    await customFetch({ url: '/health/live', method: 'GET' });

    const [, init] = spy.mock.calls[0];
    expect((init?.headers as Record<string, string>)['x-user-id']).toBe('123456');
  });

  it('adds X-Correlation-ID header', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );

    await customFetch({ url: '/health/live', method: 'GET' });

    const [, init] = spy.mock.calls[0];
    expect((init?.headers as Record<string, string>)['X-Correlation-ID']).toBeDefined();
  });

  it('throws ApiError on non-ok response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 }),
    );

    await expect(
      customFetch({ url: '/api/v1/meals/unknown', method: 'GET' }),
    ).rejects.toThrow(ApiError);
  });

  it('returns undefined for 204 responses', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(null, { status: 204 }),
    );

    const result = await customFetch({ url: '/api/v1/meals/1', method: 'DELETE' });
    expect(result).toBeUndefined();
  });
});
