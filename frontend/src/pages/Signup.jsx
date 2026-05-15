import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { signup, saveAuthSession } from "../api/auth"
import { validateSignup } from "../utils/validation"

export default function GraphRAGSignup() {
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fieldErrors, setFieldErrors] = useState({})
  const [formError, setFormError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError("")

    const errors = validateSignup({ username, email, password })
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return

    setLoading(true)
    try {
      const data = await signup({
        username: username.trim(),
        email: email.trim(),
        password,
      })
      saveAuthSession(data)
      navigate("/dashboard")
    } catch (error) {
      setFormError(error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-white">
      <div
        className="absolute inset-0 bg-cover bg-center blur-[2px] scale-110"
        style={{ backgroundImage: "url('/bg_img.jpg')" }}
      />
      <div className="absolute inset-0 bg-black/70" />

      <div className="relative z-10 flex min-h-screen items-center justify-center p-6">
        <div className="grid w-full max-w-5xl overflow-hidden rounded-3xl border border-white/10 bg-white/10 backdrop-blur-xl shadow-2xl md:grid-cols-2">
          <div className="flex flex-col justify-between bg-black/40 p-10">
            <div>
              <h1 className="text-5xl font-bold tracking-tight">GraphRAG</h1>
              <p className="mt-6 text-base leading-relaxed text-gray-300">
                Enterprise Hybrid GraphRAG platform with Neo4j, semantic
                retrieval, security guardrails, and AI-powered supply chain
                intelligence.
              </p>
            </div>

            <div className="mt-10">
              <p className="mb-4 text-sm text-gray-400">Already have an account?</p>
              <button
                type="button"
                onClick={() => navigate("/")}
                className="w-full rounded-2xl border border-white/20 bg-white/10 px-5 py-3 text-sm font-medium transition hover:bg-white hover:text-black"
              >
                Login
              </button>
            </div>
          </div>

          <div className="flex items-center justify-center p-10">
            <div className="w-full max-w-md">
              <div className="mb-8">
                <h2 className="text-3xl font-semibold">Create Account</h2>
                <p className="mt-2 text-sm text-gray-400">
                  Sign up to access the GraphRAG dashboard.
                </p>
              </div>

              <form className="space-y-5" onSubmit={handleSubmit} noValidate>
                {formError && (
                  <p className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {formError}
                  </p>
                )}

                <div>
                  <label className="mb-2 block text-sm text-gray-300">Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter your username"
                    className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none transition focus:border-white/40"
                  />
                  {fieldErrors.username && (
                    <p className="mt-2 text-sm text-red-300">{fieldErrors.username}</p>
                  )}
                </div>

                <div>
                  <label className="mb-2 block text-sm text-gray-300">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none transition focus:border-white/40"
                  />
                  {fieldErrors.email && (
                    <p className="mt-2 text-sm text-red-300">{fieldErrors.email}</p>
                  )}
                </div>

                <div>
                  <label className="mb-2 block text-sm text-gray-300">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Create your password"
                    className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none transition focus:border-white/40"
                  />
                  {fieldErrors.password && (
                    <p className="mt-2 text-sm text-red-300">{fieldErrors.password}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-2xl bg-white px-5 py-3 font-semibold text-black transition hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? "Creating account..." : "Sign Up"}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
