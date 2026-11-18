import { BookOpen, CheckCircle, Clock, AlertTriangle } from 'lucide-react'

export function Revisao() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">🔄 Caderno de Erros</h1>

      {/* Resumo */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Pendentes hoje', valor: 12, cor: 'text-danger-500', icon: AlertTriangle },
          { label: 'Esta semana', valor: 28, cor: 'text-amber-500', icon: Clock },
          { label: 'Dominadas', valor: 156, cor: 'text-success-500', icon: CheckCircle },
          { label: 'Total de erros', valor: 47, cor: 'text-primary-800', icon: BookOpen },
        ].map(s => (
          <div key={s.label} className="card text-center p-4">
            <s.icon className={`w-6 h-6 mx-auto mb-2 ${s.cor}`} />
            <p className={`text-2xl font-bold ${s.cor}`}>{s.valor}</p>
            <p className="text-xs text-[var(--color-text-light)]">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Filtros */}
      <div className="flex gap-2 flex-wrap">
        {['Todas', 'Português', 'Dir. Const.', 'CTB', 'RLM'].map(f => (
          <button key={f} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            f === 'Todas' ? 'bg-primary-800 text-white' : 'bg-[var(--color-card)] border border-[var(--color-border)] hover:border-primary-500'
          }`}>{f}</button>
        ))}
      </div>

      {/* Lista de erros */}
      <div className="space-y-3">
        {[
          { topico: 'Português — Concordância Verbal', enunciado: 'Fazem dois anos que não chove...', data: '15/11', revisao: 'Hoje', status: 'pendente' },
          { topico: 'Dir. Const. — Art. 5º, inciso X', enunciado: 'Sobre liberdade de expressão...', data: '12/11', revisao: '18/11', status: 'pendente' },
          { topico: 'CTB — Sinalização', enunciado: 'Placa de pare obrigatório...', data: '10/11', revisao: '—', status: 'dominada' },
        ].map((q, i) => (
          <div key={i} className="card flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={`badge ${q.status === 'dominada' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {q.status === 'dominada' ? '✅ Dominada' : '🔴 Pendente'}
                </span>
                <span className="text-sm font-medium">{q.topico}</span>
              </div>
              <p className="text-sm text-[var(--color-text-light)] truncate">{q.enunciado}</p>
              <div className="flex gap-4 mt-1 text-xs text-[var(--color-text-light)]">
                <span>Errou em: {q.data}</span>
                <span>Revisão: {q.revisao}</span>
              </div>
            </div>
            <div className="flex gap-2">
              {q.status !== 'dominada' && (
                <>
                  <button className="btn-primary text-sm px-4 py-2">Revisar</button>
                  <button className="btn-secondary text-sm px-4 py-2">Dominada</button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
