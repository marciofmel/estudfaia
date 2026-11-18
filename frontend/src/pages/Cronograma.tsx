import { Calendar, Clock, BookOpen, CheckCircle } from 'lucide-react'

export function Cronograma() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold">📅 Cronograma PM-MS 2024</h1>
        <div className="flex gap-2">
          <span className="badge bg-blue-100 text-blue-700">90 dias para prova</span>
          <span className="badge bg-green-100 text-green-700">3h/dia</span>
        </div>
      </div>

      {/* Semana 1 */}
      <div className="card">
        <h2 className="font-bold text-lg mb-4">Semana 1 — Base (Português + Matemática)</h2>
        <div className="space-y-2">
          {[
            { dia: 'Segunda', atividades: [{ disc: 'Português', dur: '1.5h', topico: 'Gramática' }, { disc: 'Matemática', dur: '1.5h', topico: 'Razão e proporção' }] },
            { dia: 'Terça', atividades: [{ disc: 'Português', dur: '1.5h', topico: 'Concordância' }, { disc: 'Matemática', dur: '1.5h', topico: 'Porcentagem' }] },
            { dia: 'Quarta', atividades: [{ disc: 'Revisão', dur: '3h', topico: 'Questões erradas' }] },
            { dia: 'Quinta', atividades: [{ disc: 'Dir. Penal', dur: '2h', topico: 'Crimes contra pessoa' }, { disc: 'Legislação', dur: '1h', topico: 'Lei Orgânica' }] },
            { dia: 'Sexta', atividades: [{ disc: 'Dir. Penal', dur: '2h', topico: 'Crimes patrimônio' }, { disc: 'Legislação', dur: '1h', topico: 'Regulamento' }] },
            { dia: 'Sábado', atividades: [{ disc: 'Simulado', dur: '3h', topico: 'Parcial (30 questões)' }] },
            { dia: 'Domingo', atividades: [{ disc: 'Descanso', dur: '—', topico: 'Recuperação' }] },
          ].map(d => (
            <div key={d.dia} className="flex flex-col sm:flex-row sm:items-start gap-2 p-3 bg-[var(--color-bg)] rounded-lg">
              <span className="font-bold w-24 text-sm">{d.dia}</span>
              <div className="flex-1 flex flex-wrap gap-2">
                {d.atividades.map((a, i) => (
                  <div key={i} className="flex items-center gap-2 bg-[var(--color-card)] px-3 py-1.5 rounded-lg border border-[var(--color-border)] text-sm">
                    <BookOpen className="w-3.5 h-3.5 text-primary-800" />
                    <span className="font-medium">{a.disc}</span>
                    <span className="text-[var(--color-text-light)]">({a.dur})</span>
                    <span className="text-xs text-[var(--color-text-light)]">— {a.topico}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Legenda */}
      <div className="card">
        <h3 className="font-bold mb-2">Legenda</h3>
        <div className="flex flex-wrap gap-3 text-sm">
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-primary-800 rounded-full" /> Estudo</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-amber-500 rounded-full" /> Revisão</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-success-500 rounded-full" /> Simulado</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-gray-400 rounded-full" /> Descanso</span>
        </div>
      </div>
    </div>
  )
}
