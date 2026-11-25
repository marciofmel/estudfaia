import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, X, Clock, BarChart3, Loader2, Sparkles, ChevronRight, AlertTriangle } from 'lucide-react'
import { api } from '../lib/api'

type Alternativa = { letra: string; texto: string }
type Questao = {
  id: string
  enunciado: string
  alternativas: Alternativa[]
  disciplina: string
  topico?: string
  banca: string
  ano: number
  dificuldade: number
  total_disponiveis?: number
}
type Resultado = {
  correta: boolean
  resposta_correta: string
  explicacao: string
  explicacao_ia: { estrategia: string; passos: string[] }
  proxima_revisao: string
  intervalo_dias: number
  estatistica_acerto: number
  total_respondidas: number
  taxa_acerto: number
}

export function Questoes() {
  const [questao, setQuestao] = useState<Questao | null>(null)
  const [resposta, setResposta] = useState<string | null>(null)
  const [resultado, setResultado] = useState<Resultado | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [disciplinas, setDisciplinas] = useState<{ disciplina: string; total: number }[]>([])
  const [filtro, setFiltro] = useState('')
  const [inicio, setInicio] = useState(Date.now())
  const [segundos, setSegundos] = useState(0)
  const [stats, setStats] = useState<{ total: number; taxa: number }>({ total: 0, taxa: 0 })

  useEffect(() => {
    api<{ disciplina: string; total: number }[]>('/api/questoes/disciplinas')
      .then(setDisciplinas).catch(() => {})
    carregarStats()
  }, [])

  useEffect(() => {
    if (resultado) return
    const t = window.setInterval(() => setSegundos(Math.floor((Date.now() - inicio) / 1000)), 1000)
    return () => window.clearInterval(t)
  }, [inicio, resultado])

  useEffect(() => { carregar() }, [filtro])

  async function carregarStats() {
    try {
      const s = await api<any>('/api/questoes/estatisticas')
      setStats({ total: s.total_respondidas, taxa: s.taxa_acerto })
    } catch { /* ignora */ }
  }

  async function carregar() {
    setCarregando(true); setErro(null); setResultado(null); setResposta(null)
    try {
      const q = await api<Questao>(`/api/questoes/proxima${filtro ? `?disciplina=${encodeURIComponent(filtro)}` : ''}`)
      setQuestao(q)
      setInicio(Date.now()); setSegundos(0)
    } catch (e: any) { setErro(e.message) }
    finally { setCarregando(false) }
  }

  async function confirmar() {
    if (!resposta || !questao) return
    setEnviando(true); setErro(null)
    try {
      const r = await api<Resultado>('/api/questoes/responder', {
        method: 'POST',
        body: { questao_id: questao.id, alternativa: resposta, tempo_gasto: segundos },
      })
      setResultado(r)
      carregarStats()
    } catch (e: any) { setErro(e.message) }
    finally { setEnviando(false) }
  }

  const mmss = `${String(Math.floor(segundos / 60)).padStart(2, '0')}:${String(segundos % 60).padStart(2, '0')}`

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">📚 Questões</h1>
          <p className="text-sm text-[var(--color-text-light)]">
            {stats.total} respondidas • {stats.taxa}% de acerto
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input py-2 text-sm max-w-[200px]" value={filtro}
                  onChange={e => setFiltro(e.target.value)}>
            <option value="">Todas as disciplinas</option>
            {disciplinas.map(d => (
              <option key={d.disciplina} value={d.disciplina}>{d.disciplina} ({d.total})</option>
            ))}
          </select>
        </div>
      </div>

      {erro && (
        <div className="card border-danger-500 flex items-center gap-2 text-danger-500">
          <AlertTriangle className="w-5 h-5" /> {erro}
        </div>
      )}

      {carregando ? (
        <div className="card flex items-center justify-center py-16 text-[var(--color-text-light)]">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : questao && (
        <>
          <div className="flex items-center justify-between text-sm text-[var(--color-text-light)]">
            <span>{questao.disciplina} — {questao.banca} {questao.ano}</span>
            <span className="flex items-center gap-1"><Clock className="w-4 h-4" /> {mmss}</span>
          </div>

          <div className="card">
            <span className="badge bg-primary-100 text-primary-800 mb-3 inline-block">
              {questao.topico || questao.disciplina}
            </span>
            <p className="text-lg mb-6 leading-relaxed">{questao.enunciado}</p>

            <div className="space-y-3">
              {questao.alternativas.map(alt => {
                let cls = 'border-[var(--color-border)] hover:border-primary-500'
                if (resultado) {
                  if (alt.letra === resultado.resposta_correta) cls = 'border-success-500 bg-green-50'
                  else if (alt.letra === resposta) cls = 'border-danger-500 bg-red-50'
                } else if (resposta === alt.letra) {
                  cls = 'border-primary-800 bg-primary-50'
                }
                return (
                  <button key={alt.letra} onClick={() => !resultado && setResposta(alt.letra)}
                          disabled={!!resultado}
                          className={`w-full text-left p-4 border-2 rounded-lg transition-all ${cls}`}>
                    <span className="font-bold mr-3">{alt.letra})</span>
                    {alt.texto}
                    {resultado && alt.letra === resultado.resposta_correta &&
                      <Check className="inline w-5 h-5 text-success-500 ml-2" />}
                    {resultado && alt.letra === resposta && alt.letra !== resultado.resposta_correta &&
                      <X className="inline w-5 h-5 text-danger-500 ml-2" />}
                  </button>
                )
              })}
            </div>

            {!resultado && (
              <button onClick={confirmar} disabled={!resposta || enviando}
                      className="btn-primary w-full mt-6 disabled:opacity-50 flex items-center justify-center gap-2">
                {enviando && <Loader2 className="w-4 h-4 animate-spin" />}
                {enviando ? 'Corrigindo…' : 'Confirmar Resposta'}
              </button>
            )}
          </div>

          {resultado && (
            <div className={`card ${resultado.correta ? 'border-success-500' : 'border-danger-500'}`}>
              <div className="flex items-center gap-2 mb-3">
                {resultado.correta ? <Check className="w-6 h-6 text-success-500" />
                                   : <X className="w-6 h-6 text-danger-500" />}
                <span className={`font-bold text-lg ${resultado.correta ? 'text-success-500' : 'text-danger-500'}`}>
                  {resultado.correta ? 'Correto!' : 'Incorreto'}
                </span>
                <span className="text-sm text-[var(--color-text-light)] ml-auto">
                  Gabarito: {resultado.resposta_correta}
                </span>
              </div>

              <div className="bg-[var(--color-bg)] p-4 rounded-lg mb-3">
                <p className="font-medium mb-2">📝 Explicação</p>
                <p className="text-sm leading-relaxed">{resultado.explicacao}</p>
              </div>

              <div className="bg-primary-50 p-4 rounded-lg mb-3">
                <p className="font-medium mb-2 flex items-center gap-2 text-primary-800">
                  <Sparkles className="w-4 h-4" /> Como resolver (IA)
                </p>
                <p className="text-sm leading-relaxed mb-2">{resultado.explicacao_ia.estrategia}</p>
                <ul className="text-sm space-y-1 text-[var(--color-text-light)]">
                  {resultado.explicacao_ia.passos.map((p, i) => <li key={i}>{p}</li>)}
                </ul>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-sm text-[var(--color-text-light)]">
                <span className="flex items-center gap-1">
                  <BarChart3 className="w-4 h-4" /> {resultado.estatistica_acerto}% acertam esta questão
                </span>
                <span>Próxima revisão em {resultado.intervalo_dias} dia(s)</span>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 mt-4">
                <button onClick={carregar} className="btn-primary flex-1 flex items-center justify-center gap-1">
                  Próxima questão <ChevronRight className="w-4 h-4" />
                </button>
                <Link to="/revisao" className="btn-secondary text-center">Caderno de erros</Link>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
