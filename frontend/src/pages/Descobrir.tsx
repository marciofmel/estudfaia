import { Check, X, Bookmark } from 'lucide-react'

export function Descobrir() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">🔍 Descobrir Concursos</h1>

      {/* Preferências */}
      <div className="card">
        <h2 className="font-bold mb-3">⚙️ Preferências de Busca</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Áreas de interesse</label>
            <div className="flex gap-2 flex-wrap">
              {['Policial', 'Tribunal', 'Administrativo', 'Bancário'].map(a => (
                <button key={a} className="badge bg-primary-100 text-primary-800 cursor-pointer hover:bg-primary-200">{a}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Regiões</label>
            <div className="flex gap-2 flex-wrap">
              {['MS', 'SP', 'Nacional'].map(r => (
                <button key={r} className="badge bg-primary-100 text-primary-800 cursor-pointer hover:bg-primary-200">{r}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Novos Editais */}
      <div>
        <h2 className="font-bold text-lg mb-3">🆕 Novos Editais (3)</h2>
        <div className="space-y-3">
          {[
            { titulo: 'PM-MS 2024 — Soldado PM', orgao: 'Polícia Militar MS', banca: 'Quadrix', prova: '15/02/2025', salario: 'R$ 4.500', compat: 85 },
            { titulo: 'TJ-MS 2024 — Técnico Judiciário', orgao: 'Tribunal de Justiça MS', banca: 'FCC', prova: '20/03/2025', salario: 'R$ 5.200', compat: 72 },
            { titulo: 'PRF 2024 — Policial Rodoviário', orgao: 'Polícia Rodoviária Federal', banca: 'Cebraspe', prova: '15/03/2025', salario: 'R$ 11.500', compat: 90 },
          ].map(e => (
            <div key={e.titulo} className="card">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex-1">
                  <h3 className="font-bold">{e.titulo}</h3>
                  <p className="text-sm text-[var(--color-text-light)]">{e.orgao} • {e.banca}</p>
                  <div className="flex gap-3 mt-1 text-sm">
                    <span>📅 {e.prova}</span>
                    <span>💰 {e.salario}</span>
                    <span className={`font-bold ${e.compat >= 80 ? 'text-success-500' : 'text-primary-800'}`}>🎯 {e.compat}%</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="btn-primary text-sm px-4 py-2 flex items-center gap-1"><Check className="w-4 h-4" /> Interesse</button>
                  <button className="btn-secondary text-sm px-4 py-2 flex items-center gap-1"><X className="w-4 h-4" /> Descartar</button>
                  <button className="p-2 hover:bg-gray-100 rounded-lg"><Bookmark className="w-5 h-5 text-[var(--color-text-light)]" /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Editais Passados */}
      <div>
        <h2 className="font-bold text-lg mb-3">📚 Estudar com Edital Passado</h2>
        <div className="card">
          <p className="text-sm text-[var(--color-text-light)] mb-3">Sem concurso aberto? Estude com editais anteriores.</p>
          <div className="space-y-2">
            {[
              { titulo: 'PM-MS 2022', banca: 'Quadrix', info: 'Mesma banca provável' },
              { titulo: 'PM-SP 2023', banca: 'VUNESP', info: 'Banca diferente' },
            ].map(e => (
              <div key={e.titulo} className="flex items-center justify-between p-3 bg-[var(--color-bg)] rounded-lg">
                <div>
                  <p className="font-medium">{e.titulo}</p>
                  <p className="text-sm text-[var(--color-text-light)]">{e.banca} • {e.info}</p>
                </div>
                <button className="btn-secondary text-sm px-4 py-2">Usar como base</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
