import { useEffect, useState } from 'react'
import {
  FileText, Loader2, AlertTriangle, Play, Clock, Check, ChevronLeft, Trophy, Send
} from 'lucide-react'
import { api } from '../lib/api'

type Disponivel = { id: string; titulo: string; banca: string; questoes: number; tempo_min: number }
type Lista = { disponiveis: Disponivel[]; realizados: number; media_aproveitamento: number }
type Questao = {
  id: string; enunciado: string; alternativas: { letra: string; texto: string }[]
  disciplina: string; banca: string; ano: number
}
type Simulado = { simulado_id: number; titulo: string; questoes: Questao[]; tempo_min: number }
type Resultado = {
  acertos: number; total: number; aproveitamento: number
  detalhes: { questao_id: string; marcada: string; correta: string; acertou: boolean }[]
}

export function Simulados() {
  const [lista, setLista] = useState<Lista | null>(null)
  const [historico, setHistorico] = useState<any[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [simulado, setSimulado] = useState<Simulado | null>(null)
  const [respostas, setRespostas] = useState<Record<string, string>>({})
  const [resultado, setResultado] = useState<Resultado | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [restante, setRestante] = useState(0)
  const [quantidade, setQuantidade] = useState(10)

  useEffect(() => { carregar() }, [])

  useEffect(() => {
    if (!simulado || resultado) return
    const t = window.setInterval(() => {
      setRestante(s => {
        if (s <= 1) { window.clearInterval(t); return 0 }
        return s - 1
      })
    }, 1000)
    return () => window.clearInterval(t)
  }, [simulado, resultado])

  async function carregar() {
    setCarregando(true); setErro(null)
    try {
      const [l, h] = await Promise.all([
        api<Lista>('/api/simulados'),
        api<any[]>('/api/simulados/historico'),
      ])
      setLista(l); setHistorico(h)
    } catch (e: any) { setErro(e.message) }
    finally { setCarregando(false) }
  }

  async function iniciar(concursoId?: string) {
    setErro(null); setResultado(null); setRespostas({})
    try {
      const s = await api<Simulado>('/api/simulados/iniciar', {
        method: 'POST',
        body: { concurso_id: concursoId, quantidade },
      })
      setSimulado(s)
      setRestante(s.tempo_min * 60)
    } catch (e: any) { setErro(e.message) }
  }

  async function finalizar() {
    if (!simulado) return
    setEnviando(true); setErro(null)
    try {
      const r = await api<Resultado>(`/api/simulados/${simulado.simulado_id}/finalizar`, {
        method: 'POST', body: { respostas },
      })
      setResultado(r)
      carregar()
    } catch (e: any) { setErro(e.message) }
    finally { setEnviando(false) }
  }

  const mmss = `${String(Math.floor(restante / 60)).padStart(2, '0')}:${String(restante % 60).padStart(2, '0')}`
  const respondidas = Object.keys(respostas).length

  // ---------- resultado ----------
  if (simulado && resultado) {
    return (
      <div className="max-w-3xl mx-auto space-y-5">
        <button onClick={() => { setSimulado(null); setResultado(null) }}
                className="flex items-center gap-1 text-sm text-[var(--color-text-light)]">
          <ChevronLeft className="w-4 h-4" /> Voltar aos simulados
        </button>

        <div className="card text-center">
          <Trophy className="w-12 h-12 mx-auto text-amber-500 mb-2" />
          <h1 className="text-2xl font-bold mb-1">{resultado.aproveitamento}% de aproveitamento</h1>
          <p className="text-[var(--color-text-light)]">
            {resultado.acertos} acertos em {resultado.total} questões
          </p>
        </div>

        <div className="space-y-2">
          {resultado.detalhes.map((d, i) => {
            const q = simulado.questoes.find(x => x.id === d.questao_id)
            return (
              <div key={d.questao_id} className="card flex items-start gap-3">
                <span className={`badge ${d.acertou ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} shrink-0`}>
                  {i + 1}
                </span>
                <div className="flex-1 text-sm">
                  <p className="line-clamp-2">{q?.enunciado}</p>
                  <p className="text-xs text-[var(--color-text-light)] mt-1">
                    Sua resposta: <b>{d.marcada || '—'}</b> • Gabarito: <b>{d.correta}</b>
                  </p>
                </div>
                {d.acertou ? <Check className="w-5 h-5 text-success-500" /> : null}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  // ---------- simulado em andamento ----------
  if (simulado) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <button onClick={() => setSimulado(null)} className="flex items-center gap-1 text-sm text-[var(--color-text-light)]">
            <ChevronLeft className="w-4 h-4" /> Sair
          </button>
          <span className="text-sm font-medium">{simulado.titulo}</span>
          <span className={`flex items-center gap-1 text-sm font-mono ${restante < 300 ? 'text-danger-500' : ''}`}>
            <Clock className="w-4 h-4" /> {mmss}
          </span>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div className="bg-primary-800 h-1.5 rounded-full transition-all"
               style={{ width: `${(respondidas / simulado.questoes.length) * 100}%` }} />
        </div>

        {erro && <div className="card border-danger-500 text-danger-500 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" /> {erro}</div>}

        <div className="space-y-4">
          {simulado.questoes.map((q, idx) => (
            <div key={q.id} className="card">
              <p className="text-xs text-[var(--color-text-light)] mb-2">
                Questão {idx + 1} • {q.disciplina} • {q.banca} {q.ano}
              </p>
              <p className="mb-3 leading-relaxed">{q.enunciado}</p>
              <div className="space-y-2">
                {q.alternativas.map(alt => (
                  <button key={alt.letra}
                          onClick={() => setRespostas(r => ({ ...r, [q.id]: alt.letra }))}
                          className={`w-full text-left p-3 border-2 rounded-lg text-sm transition-all ${
                            respostas[q.id] === alt.letra
                              ? 'border-primary-800 bg-primary-50'
                              : 'border-[var(--color-border)] hover:border-primary-500'
                          }`}>
                    <span className="font-bold mr-2">{alt.letra})</span>{alt.texto}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        <button onClick={finalizar} disabled={enviando}
                className="btn-primary w-full flex items-center justify-center gap-2">
          {enviando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Finalizar simulado ({respondidas}/{simulado.questoes.length})
        </button>
      </div>
    )
  }

  // ---------- lista ----------
  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">📝 Simulados</h1>
          <p className="text-sm text-[var(--color-text-light)]">
            {lista?.realizados ?? 0} feitos • média {lista?.media_aproveitamento ?? 0}%
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input py-1.5 text-sm w-32" value={quantidade}
                  onChange={e => setQuantidade(Number(e.target.value))}>
            {[5, 10, 20, 30].map(q => <option key={q} value={q}>{q} questões</option>)}
          </select>
        </div>
      </div>

      {erro && <div className="card border-danger-500 flex items-center gap-2 text-danger-500">
        <AlertTriangle className="w-5 h-5" /> {erro}</div>}

      {carregando ? (
        <div className="card flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin" /></div>
      ) : (
        <div className="space-y-3">
          {(lista?.disponiveis || []).map(d => (
            <div key={d.id} className="card flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="font-bold">{d.titulo}</h3>
                <p className="text-sm text-[var(--color-text-light)]">
                  {d.banca} • {d.questoes} questões disponíveis • {d.tempo_min} min
                </p>
              </div>
              <button onClick={() => iniciar(d.id)} className="btn-primary text-sm px-4 py-2 flex items-center gap-1">
                <Play className="w-4 h-4" /> Iniciar
              </button>
            </div>
          ))}
          <div className="card flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="font-bold flex items-center gap-2"><FileText className="w-4 h-4" /> Simulado misto</h3>
              <p className="text-sm text-[var(--color-text-light)]">Questões aleatórias de todas as disciplinas</p>
            </div>
            <button onClick={() => iniciar()} className="btn-secondary text-sm px-4 py-2 flex items-center gap-1">
              <Play className="w-4 h-4" /> Iniciar
            </button>
          </div>
        </div>
      )}

      {historico.length > 0 && (
        <div className="card">
          <h2 className="font-bold mb-3">Histórico</h2>
          <div className="space-y-1">
            {historico.slice(0, 8).map(h => (
              <div key={h.id} className="flex items-center justify-between text-sm p-2 bg-[var(--color-bg)] rounded">
                <span className="truncate">{h.titulo}</span>
                <span className="font-bold shrink-0">
                  {h.acertos ?? 0}/{h.total} ({h.aproveitamento}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
