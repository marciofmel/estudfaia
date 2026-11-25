import { useEffect, useState } from 'react'
import { Calendar, Clock, BookOpen, RefreshCw, Loader2, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { api, dataBR } from '../lib/api'

type Atividade = { disciplina: string; topico: string; duracao_h: number; tipo: string }
type Dia = { data: string; dia_semana: string; atividades: Atividade[] }
type Semana = { semana: number; dias: Dia[] }
type Plano = {
  existe?: boolean
  concurso_id?: string | null
  data_prova?: string
  dias_restantes?: number
  horas_dia?: number
  semanas?: number
  total_horas?: number
  distribuicao?: { disciplina: string; peso_pct: number }[]
  plano?: Semana[]
}

const COR: Record<string, string> = {
  estudo: 'bg-blue-100 text-blue-700',
  revisao: 'bg-amber-100 text-amber-700',
  simulado: 'bg-green-100 text-green-700',
}

export function Cronograma() {
  const [plano, setPlano] = useState<Plano | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [gerando, setGerando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [horas, setHoras] = useState(3)

  useEffect(() => { carregar() }, [])

  async function carregar() {
    setCarregando(true); setErro(null)
    try { setPlano(await api<Plano>('/api/cronograma')) }
    catch (e: any) { setErro(e.message) }
    finally { setCarregando(false) }
  }

  async function gerar() {
    setGerando(true); setErro(null)
    try {
      const p = await api<Plano>('/api/cronograma/gerar', {
        method: 'POST',
        body: { horas_dia: horas, incluir_domingo: false },
      })
      setPlano(p)
    } catch (e: any) { setErro(e.message) }
    finally { setGerando(false) }
  }

  const hoje = new Date().toISOString().slice(0, 10)
  const primeiraSemana = plano?.plano?.[0]

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">📅 Meu Cronograma</h1>
          <p className="text-sm text-[var(--color-text-light)]">
            Gerado pela IA a partir das disciplinas do seu concurso
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {plano?.dias_restantes != null && (
            <span className="badge bg-blue-100 text-blue-700">{plano.dias_restantes} dias para a prova</span>
          )}
          <select className="input py-1.5 text-sm w-28" value={horas}
                  onChange={e => setHoras(Number(e.target.value))}>
            {[1, 2, 3, 4, 5, 6].map(h => <option key={h} value={h}>{h}h/dia</option>)}
          </select>
          <button onClick={gerar} disabled={gerando} className="btn-primary text-sm flex items-center gap-2">
            {gerando ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            {gerando ? 'Gerando…' : 'Gerar com IA'}
          </button>
        </div>
      </div>

      {erro && <div className="card border-danger-500 flex items-center gap-2 text-danger-500">
        <AlertTriangle className="w-5 h-5" /> {erro}</div>}

      {carregando ? (
        <div className="card flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin" /></div>
      ) : (
        <>
          {/* Resumo */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              ['Semanas', plano?.semanas ?? 0],
              ['Horas totais', plano?.total_horas ?? 0],
              ['Prova', dataBR(plano?.data_prova)],
              ['Horas/dia', plano?.horas_dia ?? horas],
            ].map(([label, valor]) => (
              <div key={String(label)} className="card py-3 text-center">
                <p className="text-xs text-[var(--color-text-light)]">{label}</p>
                <p className="font-bold text-lg">{String(valor)}</p>
              </div>
            ))}
          </div>

          {/* Distribuição */}
          {plano?.distribuicao && (
            <div className="card">
              <h2 className="font-bold mb-3">Peso de cada disciplina</h2>
              <div className="space-y-1.5">
                {plano.distribuicao.map(d => (
                  <div key={d.disciplina} className="flex items-center gap-2 text-sm">
                    <span className="w-40 shrink-0 truncate">{d.disciplina}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div className="bg-primary-800 h-2 rounded-full" style={{ width: `${Math.min(100, d.peso_pct)}%` }} />
                    </div>
                    <span className="w-12 text-right text-[var(--color-text-light)]">{d.peso_pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Primeira semana em destaque */}
          {primeiraSemana && (
            <div className="card">
              <h2 className="font-bold text-lg mb-3 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-primary-800" /> Semana 1
              </h2>
              <div className="space-y-2">
                {primeiraSemana.dias.map(d => (
                  <div key={d.data}
                       className={`flex flex-col sm:flex-row sm:items-start gap-2 p-3 rounded-lg ${d.data === hoje ? 'bg-primary-50 border border-primary-200' : 'bg-[var(--color-bg)]'}`}>
                    <div className="sm:w-32 shrink-0">
                      <span className="font-bold text-sm">{d.dia_semana}</span>
                      <span className="text-xs text-[var(--color-text-light)] block">{dataBR(d.data)}</span>
                    </div>
                    <div className="flex-1 flex flex-wrap gap-2">
                      {d.atividades.map((a, i) => (
                        <div key={i} className="flex items-center gap-2 bg-[var(--color-card)] px-3 py-1.5 rounded-lg border border-[var(--color-border)] text-sm">
                          <BookOpen className="w-3.5 h-3.5 text-primary-800" />
                          <span className="font-medium">{a.disciplina}</span>
                          <span className="text-[var(--color-text-light)]">({a.duracao_h}h)</span>
                          <span className="text-xs text-[var(--color-text-light)] max-w-[220px] truncate">— {a.topico}</span>
                          <span className={`badge text-[10px] ${COR[a.tipo] || 'bg-gray-100 text-gray-600'}`}>{a.tipo}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Demais semanas */}
          {plano?.plano && plano.plano.length > 1 && (
            <div className="card">
              <h2 className="font-bold text-lg mb-3">Próximas semanas</h2>
              <details className="group">
                <summary className="cursor-pointer text-sm text-primary-800 flex items-center gap-1">
                  <Clock className="w-4 h-4" /> Ver as {plano.plano.length - 1} semanas restantes
                </summary>
                <div className="mt-3 space-y-3">
                  {plano.plano.slice(1).map(s => (
                    <div key={s.semana} className="border-l-2 border-primary-200 pl-3">
                      <p className="font-medium text-sm mb-1">Semana {s.semana}</p>
                      <div className="space-y-1">
                        {s.dias.map(d => (
                          <p key={d.data} className="text-xs text-[var(--color-text-light)]">
                            <b className="text-[var(--color-text)]">{d.dia_semana}</b> —{' '}
                            {d.atividades.map(a => a.disciplina).join(' • ')}
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}

          {!plano?.plano?.length && (
            <div className="card text-center py-10 text-[var(--color-text-light)]">
              <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-primary-800" />
              Clique em "Gerar com IA" para montar seu plano de estudos.
            </div>
          )}
        </>
      )}
    </div>
  )
}
