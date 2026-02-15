const SESSION_CORRELATION_ID = crypto.randomUUID();

function getTelegramUserId(): string | undefined {
  return window.Telegram?.WebApp?.initDataUnsafe?.user?.id?.toString();
}

function getBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
}

export async function customFetch<T>(
  urlOrConfig:
    | string
    | {
        url: string;
        method: string;
        params?: Record<string, string>;
        data?: unknown;
        headers?: Record<string, string>;
        signal?: AbortSignal;
      },
  init?: RequestInit,
): Promise<T> {
  const baseUrl = getBaseUrl();

  let fullUrl: string;
  let method: string;
  let body: string | undefined;
  let extraHeaders: Record<string, string> | undefined;
  let signal: AbortSignal | undefined;

  if (typeof urlOrConfig === "string") {
    // Orval-generated call: customFetch(url, { method, headers, body, signal })
    fullUrl = `${baseUrl}${urlOrConfig}`;
    method = init?.method ?? "GET";
    body = init?.body as string | undefined;
    extraHeaders = init?.headers as Record<string, string> | undefined;
    signal = init?.signal ?? undefined;
  } else {
    // Legacy call: customFetch({ url, method, params, data, ... })
    const {
      url,
      params,
      data,
      headers: cfgHeaders,
      signal: cfgSignal,
    } = urlOrConfig;
    method = urlOrConfig.method;
    const queryString = params
      ? "?" + new URLSearchParams(params).toString()
      : "";
    fullUrl = `${baseUrl}${url}${queryString}`;
    body = data ? JSON.stringify(data) : undefined;
    extraHeaders = cfgHeaders;
    signal = cfgSignal;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Correlation-ID": SESSION_CORRELATION_ID,
    ...extraHeaders,
  };

  const userId = getTelegramUserId();
  if (userId) {
    headers["x-user-id"] = userId;
  }

  const response = await fetch(fullUrl, {
    method,
    headers,
    body,
    signal,
  });

  if (!response.ok) {
    const errorBody = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, errorBody.detail ?? "Request failed");
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
    this.name = "ApiError";
  }
}
