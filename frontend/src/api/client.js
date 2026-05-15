const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8001"

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  })

  let data = null
  const contentType = response.headers.get("content-type") || ""
  if (contentType.includes("application/json")) {
    data = await response.json()
  }

  if (!response.ok) {
    let message = "Request failed. Please try again."
    if (typeof data?.detail === "string") {
      message = data.detail
    } else if (Array.isArray(data?.detail)) {
      message = data.detail
        .map((item) => item.msg || item.message || String(item))
        .join(", ")
    }
    throw new Error(message)
  }

  return data
}
