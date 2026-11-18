import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Home, BookOpen, FileText, Calendar, RotateCcw,
  Search, User, Menu, X, Bell, Sun, Moon, Zap
} from 'lucide-react'

const navItems = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/questoes', icon: BookOpen, label: 'Questões' },
  { path: '/simulados', icon: FileText, label: 'Simulados' },
  { path: '/cronograma', icon: Calendar, label: 'Cronograma' },
  { path: '/revisao', icon: RotateCcw, label: 'Revisão' },
  { path: '/descobrir', icon: Search, label: 'Descobrir' },
  { path: '/perfil', icon: User, label: 'Perfil' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const location = useLocation()

  const toggleDark = () => {
    setDarkMode(!darkMode)
    document.documentElement.classList.toggle('dark')
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar Desktop */}
      <aside className="hidden lg:flex flex-col w-60 bg-[var(--color-card)] border-r border-[var(--color-border)] fixed h-full z-30">
        <div className="p-6 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-800 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg">ConcursosAI</span>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(item => {
            const active = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  active
                    ? 'bg-primary-800 text-white shadow-md'
                    : 'text-[var(--color-text-light)] hover:bg-primary-50 hover:text-primary-800'
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>
        <div className="p-4 border-t border-[var(--color-border)]">
          <button onClick={toggleDark} className="flex items-center gap-3 px-4 py-3 rounded-lg text-[var(--color-text-light)] hover:bg-primary-50 w-full transition-all">
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            <span className="font-medium">{darkMode ? 'Modo Claro' : 'Modo Escuro'}</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-14 bg-[var(--color-card)] border-b border-[var(--color-border)] z-40 flex items-center justify-between px-4">
        <button onClick={() => setSidebarOpen(true)} className="p-2">
          <Menu className="w-6 h-6" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-primary-800 rounded-lg flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold">ConcursosAI</span>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 relative">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-danger-500 rounded-full" />
          </button>
        </div>
      </header>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-72 bg-[var(--color-card)] shadow-xl">
            <div className="p-4 flex justify-between items-center border-b border-[var(--color-border)]">
              <span className="font-bold text-lg">Menu</span>
              <button onClick={() => setSidebarOpen(false)}><X className="w-6 h-6" /></button>
            </div>
            <nav className="p-4 space-y-1">
              {navItems.map(item => {
                const active = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                      active ? 'bg-primary-800 text-white' : 'text-[var(--color-text-light)] hover:bg-primary-50'
                    }`}
                  >
                    <item.icon className="w-5 h-5" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                )
              })}
            </nav>
          </aside>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 lg:ml-60 pt-14 lg:pt-0 pb-20 lg:pb-0">
        <div className="max-w-7xl mx-auto p-4 lg:p-8">
          {children}
        </div>
      </main>

      {/* Bottom Nav Mobile */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 h-16 bg-[var(--color-card)] border-t border-[var(--color-border)] z-40 flex items-center justify-around">
        {navItems.slice(0, 5).map(item => {
          const active = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-all ${
                active ? 'text-primary-800' : 'text-[var(--color-text-light)]'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
