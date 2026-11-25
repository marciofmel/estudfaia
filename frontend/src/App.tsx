import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Questoes } from './pages/Questoes'
import { Simulados } from './pages/Simulados'
import { Cronograma } from './pages/Cronograma'
import { Revisao } from './pages/Revisao'
import { Perfil } from './pages/Perfil'
import { Login } from './pages/Login'
import { Descobrir } from './pages/Descobrir'
import { api, getToken, setToken } from './lib/api'

function AppRoutes() {
  const [estado, setEstado] = useState<'checando' | 'logado' | 'deslogado'>('checando')
  const [erro, setErro] = useState<string | null>(null)
  const location = useLocation()

  useEffect(() => {
    (async () => {
      if (getToken()) { setEstado('logado'); return }
      // sem token: tenta entrar na conta demo automaticamente (app sempre usável)
      try {
        const r = await api<{ access_token: string }>('/api/auth/demo', { method: 'POST', body: {} })
        if (r?.access_token) { setToken(r.access_token); setEstado('logado'); return }
        setEstado('deslogado')
      } catch {
        // backend ainda subindo
        setErro('Não foi possível falar com a API (localhost:8000).')
        setEstado('deslogado')
      }
    })()
  }, [])

  if (estado === 'checando') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-3 text-[var(--color-text-light)]">
        <Loader2 className="w-7 h-7 animate-spin" />
        <p className="text-sm">Conectando ao ConcursosAI…</p>
        {erro && <p className="text-xs text-danger-500">{erro}</p>}
      </div>
    )
  }

  if (estado === 'deslogado' || location.pathname === '/login') {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/questoes" element={<Questoes />} />
        <Route path="/simulados" element={<Simulados />} />
        <Route path="/cronograma" element={<Cronograma />} />
        <Route path="/revisao" element={<Revisao />} />
        <Route path="/descobrir" element={<Descobrir />} />
        <Route path="/perfil" element={<Perfil />} />
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
