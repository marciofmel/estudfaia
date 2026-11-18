import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Questoes } from './pages/Questoes'
import { Simulados } from './pages/Simulados'
import { Cronograma } from './pages/Cronograma'
import { Revisao } from './pages/Revisao'
import { Perfil } from './pages/Perfil'
import { Login } from './pages/Login'
import { Descobrir } from './pages/Descobrir'

export default function App() {
  const [isAuthenticated] = useState(true) // Mock

  if (!isAuthenticated) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    )
  }

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/questoes" element={<Questoes />} />
          <Route path="/simulados" element={<Simulados />} />
          <Route path="/cronograma" element={<Cronograma />} />
          <Route path="/revisao" element={<Revisao />} />
          <Route path="/descobrir" element={<Descobrir />} />
          <Route path="/perfil" element={<Perfil />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
