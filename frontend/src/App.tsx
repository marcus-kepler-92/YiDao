import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import ChatPage from "@/pages/ChatPage"
import LoginPage from "@/pages/LoginPage"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:bucketId" element={<ChatPage />} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
