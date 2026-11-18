import { useState } from 'react'
import { Play, Clock, FileText, Users } from 'lucide-react'

export function Simulados() {
  const [modo, setModo] = useState<'lista' | 'prova'>('lista')

  if (modo === 'prova') {
    return (
      <div className="fixed inset-0 bg-[var(--color-bg)] z-50 flex flex-col">
        <header className="bg-danger-500 text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            <span className="font-bold">SIMULADO PRF 2024 — Prova Real</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="font-mono text-lg">03:45:12</span>
            <span className="text-sm">Questão 45/120</span>
          </div>
        </header>
        <div className="flex-1 p-4 max-w-4xl mx-auto w-full">
          <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
            <div className="bg-danger-500 h-2 rounded-full" style={{ width: '37.5%' }} />
          </div>
          <div className="card">
            <p className="text-lg mb-6">Qual é a velocidade máxima permitida em rodovias de pista dupla para veículos de passeio?</p>
            <div className="space-y-3">
              {['80 km/h', '100 km/h', '110 km/h', '120 km/h'].map((alt, i) => (
                <button key={i} className="w-full text-left p-4 border-2 border-[var(--color-border)] rounded-lg hover:border-danger-500 transition-all">
                  <span className="font-bold mr-3">{String.fromCharCode(65 + i)})</span>{alt}
                </button>
              ))}
            </div>
          </div>
        </div>
        <footer className="p-4 flex justify-between max-w-4xl mx-auto w-full">
          <button className="btn-secondary">◀ Anterior</button>
          <button className="btn-accent">Finalizar Simulado</button>
          <button className="btn-primary">Próxima ▶</button>
        </footer>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">📝 Simulados</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { titulo: 'PRF 2024 — Prova Completa', questoes: 120, tempo: '4h30', alunos: 1250, cor: 'bg-primary-800' },
          { titulo: 'PM-MS 2024 — Soldado', questoes: 80, tempo: '3h', alunos: 890, cor: 'bg-amber-500' },
          { titulo: 'INSS 2024 — Técnico', questoes: 60, tempo: '3h30', alunos: 2100, cor: 'bg-success-500' },
        ].map(s => (
          <div key={s.titulo} className="card">
            <div className={`w-12 h-12 ${s.cor} rounded-xl flex items-center justify-center mb-3`}>
              <FileText className="w-6 h-6 text-white" />
            </div>
            <h3 className="font-bold text-lg mb-2">{s.titulo}</h3>
            <div className="flex gap-4 text-sm text-[var(--color-text-light)] mb-4">
              <span className="flex items-center gap-1"><FileText className="w-4 h-4" />{s.questoes} questões</span>
              <span className="flex items-center gap-1"><Clock className="w-4 h-4" />{s.tempo}</span>
              <span className="flex items-center gap-1"><Users className="w-4 h-4" />{s.alunos}</span>
            </div>
            <button onClick={() => setModo('prova')} className="btn-primary w-full flex items-center justify-center gap-2">
              <Play className="w-4 h-4" /> Iniciar Simulado
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
