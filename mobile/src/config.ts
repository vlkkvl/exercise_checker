// Set EXPO_PUBLIC_API_URL in your .env to point to your backend.
// Default falls back to localhost for local dev.
export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
