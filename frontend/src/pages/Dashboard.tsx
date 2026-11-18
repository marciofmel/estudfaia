import React from 'react'
import { Link } from 'react-router-dom'
import { Zap, BookOpen, FileText, Calendar, Search, TrendingUp, Flame, Target } from 'lucide-react'

export function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Bom dia, João! 👋</h1>
          <p className="text-[var(--color-text-light)]">Você tem 12 questões para revisar hoje.</p>
        </div>
        <div className="flex items-center gap-2 bg-amber-50 text-amber-700 px-4 py-2 rounded-lg">
          <Flame className="w-5 h-5" />
          <span className="font-bold">7 dias</span>
          <span className="text-sm">de streak</span>
        </div>
      </div>

      {/* Cards de Concursos + Desempenho */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Meus Concursos */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-lg flex items-center gap-2">
              <Target className="w-5 h-5 text-primary-800" /> Meus Concursos
            </h2>
            <Link to="/descobrir" className="text-sm text-primary-800 hover:underline">+ Adicionar</Link>
          </div>
          <div className="space-y-3">
            {[
              { nome: 'PRF 2024', progresso: 78, dias: 45, cor: 'bg-primary-800' },
              { nome: 'PM-MS 2024', progresso: 0, dias: 90, cor: 'bg-amber-500' },
            ].map(c => (
              <div key={c.nome} className="p-3 bg-[var(--color-bg)] rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">{c.nome}</span>
                  <span className="text-sm text-[var(--color-text-light)]">{c.dias} dias</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className={`${c.cor} h-2 rounded-full transition-all duration-500`} style={{ width: `${c.progresso}%` }} />
                </div>
                <div className="flex justify-between mt-1">
                  <span className="text-xs text-[var(--color-text-light)]">{c.progresso}% concluído</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Desempenho Hoje */}
        <div className="card">
          <h2 className="font-bold text-lg flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-success-500" /> Desempenho Hoje
          </h2>
          <div className="flex items-center justify-center mb-4">
            <div className="relative w-32 h-32">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#E2E8F0" strokeWidth="8" />
                <circle cx="50" cy="50" r="40" fill="none" stroke="#10B981" strokeWidth="8"
                  strokeDasharray={`${80 * 2.51} ${100 * 2.51}`} strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold">80%</span>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div><p className="text-2xl font-bold text-success-500">18</p><p className="text-xs text-[var(--color-text-light)]">Acertos</p></div>
            <div><p className="text-2xl font-bold text-danger-500">6</p><p className="text-xs text-[var(--color-text-light)]">Erros</p></div>
            <div><p className="text-2xl font-bold text-primary-800">24</p><p className="text-xs text-[var(--color-text-light)]">Total</p></div>
          </div>
        </div>
      </div>

      {/* Cronograma de Hoje */}
      <div className="card">
        <h2 className="font-bold text-lg flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-primary-800" /> Cronograma de Hoje
        </h2>
        <div className="space-y-2">
          {[
            { hora: '08:00-09:30', atividade: 'Português (PRF) — Gramática e Concordância', tipo: 'estudo' },
            { hora: '09:30-10:00', atividade: 'Revisão de 12 questões erradas', tipo: 'revisao' },
            { hora: '10:00-11:30', atividade: 'CTB — Legislação de Trânsito', tipo: 'estudo' },
          ].map((a, i) => (
            <div key={i} className="flex items-center gap-4 p-3 bg-[var(--color-bg)] rounded-lg">
              <span className="text-sm font-mono text-[var(--color-text-light)] w-28">{a.hora}</span>
              <span className="flex-1 font-medium">{a.atividade}</span>
              <span className={`badge ${a.tipo === 'revisao' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                {a.tipo === 'revisao' ? 'Revisão' : 'Estudo'}
              </span>
            </div>
          ))}
        </div>
        <button className="btn-primary w-full mt-4">Iniciar Estudo</button>
      </div>

      {/* Novos Editais */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-lg flex items-center gap-2">
            <Search className="w-5 h-5 text-primary-800" /> Novos Editais
          </h2>
          <Link to="/descobrir" className="text-sm text-primary-800 hover:underline">Ver todos</Link>
        </div>
        <div className="space-y-2">
          {[
            { titulo: 'PM-MS 2024 — Soldado PM', compat: 85, prova: '15/02/2025' },
            { titulo: 'TJ-MS 2024 — Técnico', compat: 72, prova: '20/03/2025' },
          ].map(e => (
            <div key={e.titulo} className="flex items-center justify-between p-3 bg-[var(--color-bg)] rounded-lg">
              <div>
                <p className="font-medium">{e.titulo}</p>
                <p className="text-sm text-[var(--color-text-light)]">Prova: {e.prova}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`badge ${e.compat >= 80 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                  {e.compat}% compatível
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
