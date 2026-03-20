import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import LoginPage from './pages/Login'
import DashboardPage from './pages/Dashboard'
import EnterprisesPage from './pages/Enterprises'
import FinancialsPage from './pages/Financials'
import UsersPage from './pages/Users'
import AIConfigPage from './pages/AIConfig'
import AIAnalysisPage from './pages/AIAnalysis'
import MainLayout from './components/Layout/MainLayout'

// Protected Route wrapper
function ProtectedRoute() {
  const token = localStorage.getItem('access_token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/enterprises" element={<EnterprisesPage />} />
            <Route path="/financials" element={<FinancialsPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/ai-config" element={<AIConfigPage />} />
            <Route path="/ai-analysis" element={<AIAnalysisPage />} />
          </Route>
        </Route>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App