let csrf = ''
export function setCsrf(value: string) {
  csrf = value
}
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isForm = options.body instanceof FormData
  const response = await fetch(path, {
    ...options,
    credentials: 'same-origin',
    headers: {
      ...(isForm ? {} : { 'Content-Type': 'application/json' }),
      ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
      ...options.headers,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const fields = body.error?.fields
      ?.map((f: { field: string; message: string }) => `${f.field}: ${f.message}`)
      .join('; ')
    throw new ApiError(
      response.status,
      fields || body.error?.message || 'The request failed. Please try again.',
    )
  }
  return response.status === 204 ? (undefined as T) : response.json()
}
