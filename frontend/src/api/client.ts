const SESSION_CORRELATION_ID = crypto.randomUUID();

function getTelegramUserId(): string | undefined {
  return window.Telegram?.WebApp?.initDataUnsafe?.user?.id?.toString();
}

function getBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
}

export async function customFetch<T>(config: {
  url: string;
  method: string;
  params?: Record<string, string>;
  data?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}): Promise<T> {
  const { url, method, params, data, headers: extraHeaders, signal } = config;

  const baseUrl = getBaseUrl();
  const queryString = params
    ? '?' + new URLSearchParams(params).toString()
    : '';
  const fullUrl = `${baseUrl}${url}${queryString}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Correlation-ID': SESSION_CORRELATION_ID,
    ...extraHeaders,
  };

  const userId = getTelegramUserId();
  if (userId) {
    headers['x-user-id'] = userId;
  }

  const response = await fetch(fullUrl, {
    method,
    headers,
    body: data ? JSON.stringify(data) : undefined,
    signal,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, errorBody.detail ?? 'Request failed');
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
