import { getAuthSession } from "./auth"

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8001"

const RATE_LIMIT_MESSAGE =
  "Too many requests. Please wait a minute and try again."

function buildAuthHeaders() {
  const headers = {
    "Content-Type": "application/json",
  }
  const token = getAuthSession()?.token
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return headers
}

export async function sendChatMessage(query) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: buildAuthHeaders(),
    body: JSON.stringify({ query }),
  })

  let data = null
  const contentType = response.headers.get("content-type") || ""
  if (contentType.includes("application/json")) {
    data = await response.json()
  }

  if (response.status === 429) {
    const detail =
      typeof data?.detail === "string" ? data.detail : RATE_LIMIT_MESSAGE
    throw new Error(
      detail.includes("Rate limit") ? RATE_LIMIT_MESSAGE : detail
    )
  }

  if (!response.ok) {
    const message =
      typeof data?.detail === "string"
        ? data.detail
        : "Request failed. Please try again."
    throw new Error(message)
  }

  return data
}
