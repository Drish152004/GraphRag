import { apiRequest } from "./client"

export function signup({ username, email, password }) {
  return apiRequest("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  })
}

export function login({ email, password }) {
  return apiRequest("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  })
}

export function saveAuthSession(data) {
  localStorage.setItem("access_token", data.access_token)
  localStorage.setItem("user", JSON.stringify(data.user))
}

export function clearAuthSession() {
  localStorage.removeItem("access_token")
  localStorage.removeItem("user")
}

export function getAuthSession() {
  const token = localStorage.getItem("access_token")
  const userRaw = localStorage.getItem("user")
  if (!token || !userRaw) return null
  try {
    return { token, user: JSON.parse(userRaw) }
  } catch {
    clearAuthSession()
    return null
  }
}

export function isAuthenticated() {
  return Boolean(getAuthSession()?.token)
}
