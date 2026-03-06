import type { ReactElement } from "react"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import ChatPage from "@/pages/ChatPage"
import LoginPage from "@/pages/LoginPage"
import { useAuthStore } from "@/stores/authStore"

interface RequireAuthProps {
  children: ReactElement
}

function RequireAuth({ children }: RequireAuthProps) {
  const token = useAuthStore((state) => state.token)

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return children
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/chat"
          element={
            <RequireAuth>
              <ChatPage />
            </RequireAuth>
          }
        />
        <Route
          path="/chat/:bucketId"
          element={
            <RequireAuth>
              <ChatPage />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
