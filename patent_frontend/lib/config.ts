/**
 * 애플리케이션 설정
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const config = {
  apiBaseUrl: API_BASE_URL,
} as const
