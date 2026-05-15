const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateLogin({ email, password }) {
  const errors = {}

  if (!email.trim()) {
    errors.email = "Email is required."
  } else if (!EMAIL_PATTERN.test(email.trim())) {
    errors.email = "Enter a valid email address."
  }

  if (!password) {
    errors.password = "Password is required."
  }

  return errors
}

export function validateSignup({ username, email, password }) {
  const errors = {}

  if (!username.trim()) {
    errors.username = "Username is required."
  } else if (username.trim().length < 2) {
    errors.username = "Username must be at least 2 characters."
  }

  if (!email.trim()) {
    errors.email = "Email is required."
  } else if (!EMAIL_PATTERN.test(email.trim())) {
    errors.email = "Enter a valid email address."
  }

  if (!password) {
    errors.password = "Password is required."
  } else if (password.length < 6) {
    errors.password = "Password must be at least 6 characters."
  }

  return errors
}
