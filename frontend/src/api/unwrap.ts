/**
 * Extract the actual response body from an Orval hook result.
 * Orval types wrap the body in { data, status, headers } but at runtime
 * customFetch returns the raw JSON body directly.
 */
export function unwrap<T>(response: unknown): T | undefined {
  if (!response) return undefined;
  const r = response as Record<string, unknown>;
  if ("data" in r && "status" in r) {
    return r.data as T;
  }
  return response as T;
}
