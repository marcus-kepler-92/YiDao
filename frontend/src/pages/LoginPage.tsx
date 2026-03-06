import { useState } from "react"
import type { FormEvent } from "react"
import { Navigate, useNavigate } from "react-router-dom"

import { loginApiV1AuthLoginPost } from "@/api/generated/endpoints"
import { useAuthStore } from "@/stores/authStore"

const DEFAULT_LOGIN_ERROR = "登录失败，请检查账号密码后重试"

export default function LoginPage() {
  const navigate = useNavigate()
  const token = useAuthStore((state) => state.token)
  const setToken = useAuthStore((state) => state.setToken)

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  if (token) {
    return <Navigate to="/chat" replace />
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (isSubmitting) {
      return
    }

    setErrorMessage(null)
    setIsSubmitting(true)

    try {
      const response = await loginApiV1AuthLoginPost({
        username,
        password,
      })

      if (response.status !== 200) {
        throw new Error(DEFAULT_LOGIN_ERROR)
      }

      const accessToken = response.data.data?.access_token
      if (!accessToken) {
        throw new Error(DEFAULT_LOGIN_ERROR)
      }

      setToken(accessToken)
      navigate("/chat", { replace: true })
    } catch (error) {
      const message = error instanceof Error && error.message ? error.message : DEFAULT_LOGIN_ERROR
      setErrorMessage(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <form
        className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
        onSubmit={handleSubmit}
      >
        <h1 className="text-xl font-semibold text-slate-900">登录 YiDao</h1>
        <p className="mt-2 text-sm text-slate-500">请输入账号和密码继续</p>

        <div className="mt-5 space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">账号</span>
            <input
              autoComplete="username"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none ring-blue-500 transition focus:ring-2"
              onChange={(event) => setUsername(event.target.value)}
              required
              value={username}
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">密码</span>
            <input
              autoComplete="current-password"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none ring-blue-500 transition focus:ring-2"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
        </div>

        {errorMessage ? <p className="mt-4 text-sm text-red-600">{errorMessage}</p> : null}

        <button
          className="mt-6 w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSubmitting}
          type="submit"
        >
          {isSubmitting ? "登录中..." : "登录"}
        </button>
      </form>
    </div>
  )
}
