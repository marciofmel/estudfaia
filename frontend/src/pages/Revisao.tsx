import { useEffect, useState } from 'react'
import {
  RotateCcw, AlertTriangle, Loader2, Check, X, BookOpen, CalendarClock, Sparkles
} from 'lucide-react'
import { api, dataBR } from '../lib/api'

type Revisao = {
  questao_id: string; enunciado: string; disciplina: string; topico: string
  banca: string; ano: number; proxima_revisao: string; status: string
}
type Questao = {
  id: string; enunciado: string; alternativas: { letra: string; texto: string }[]
  disciplina: string; topico?: string; banca: string; ano: number
}
type Resultado = {
  correta: boolean; resposta_correta: string; explicacao: string
  explicacao_ia: { estrategia: string; passos: string[] }
  proxima_revisao: string; intervalo_dias: number
}

export function Revisao() {
  const [revisoes, setRevisoes] = useState<Revisao[]>([])
  const [erros, setErros] = useState<Revisao[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [aba, setAba] = useState<'hoje' | 'erros'>('hoje')
  const [questao, setQuestao] = useState<Questao | null>(null)
  const [resposta, setResposta] = useState<string | null>(null)
  const [resultado, setResultado] = useState<Resultado | null>(null)
  const [enviando, setEnviando] = useState(false)

  useEffect(() => { carregar() }, [])

  async function carregar() {
    setCarregando(true); setErro(null)
    try {
      const [rev, cad] = await Promise.all([
        api<any>('/api/questoes/revisoes'),
        api<any>('/api/questoes/caderno-erros'),
      ])
      setRevisoes(rev.revisoes || [])
      setErros(cad.questoes || [])
    } catch (e: any) { setErro(e.message) }
    finally { setCarregando(false) }
  }

  async function abrir(id: string) {
    setErro(null); setResultado(null); setResposta(null)
    try { setQuestao(await api<Questao>(`/api/questoes/${id}`)) }
    catch (e: any) { setErro(e.message) }
  }

  async function confirmar() {
    if (!questao || !resposta) return
    setEnviando(true)
    try {
      const r = await api<Resultado>('/api/questoes/responder', {
        method: 'POST',
        body: { questao_id: questao.id, alternativa: resposta, tempo_gasto: 0 },
      })
      setResultado(r)
      carregar()
    } catch (e: any) { setErro(e.message) }
    finally { setEnviando(false) }
  }

  const lista = aba === 'hoje' ? revisoes : erros

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div>
        <h1 className="text-2xl font-bold">🔁 Revisão Espaçada</h1>
        <p className="text-sm text-[var(--color-text-light)]">
          Intervalos calculados pelo algoritmo SM-2: 1 → 3 → 7 → 15 dias
        </p>
      </div>

      {erro && <div className="card border-danger-500 flex items-center gap-2 text-danger-500">
        <AlertTriangle className="w-5 h-5" /> {erro}</div>}

      <div className="flex gap-2">
        <button onClick={() => setAba('hoje')}
                className={`btn-${aba === 'hoje' ? 'primary' : 'secondary'} text-sm flex items-center gap-2`}>
          <CalendarClock className="w-4 h-4" /> Para hoje ({revisoes.length})
        </button>
        <button onClick={() => setAba('erros')}
                className={`btn-${aba === 'erros' ? 'primary' : 'secondary'} text-sm flex items-center gap-2`}>
          <RotateCcw className="w-4 h-4" /> Caderno de erros ({erros.length})
        </button>
      </div>

      {carregando ? (
        <div className="card flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin" /></div>
      ) : lista.length === 0 ? (
        <div className="card text-center py-12 text-[var(--color-text-light)]">
          <Check className="w-10 h-10 mx-auto mb-2 text-success-500" />
          {aba === 'hoje'
            ? 'Nenhuma revisão pendente hoje. Responda questões para alimentar a fila.'
            : 'Nenhum erro registrado ainda.'}
        </div>
      ) : (
        <div className="space-y-2">
          {lista.map(r => (
            <div key={r.questao_id} className="card flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex-1">
                <p className="font-medium line-clamp-2">{r.enunciado}</p>
                <p className="text-xs text-[var(--color-text-light)] mt-1">
                  {r.disciplina} • {r.topico} • {r.banca} {r.ano}
                  {r.proxima_revisao && ` • revisar em ${dataBR(r.proxima_revisao)}`}
                </p>
              </div>
              <button onClick={() => abrir(r.questao_id)} className="btn-secondary text-sm px-4 py-2 flex items-center gap-1">
                <BookOpen className="w-4 h-4" /> Revisar
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Questão em revisão */}
      {questao && (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <span className="badge bg-primary-100 text-primary-800">{questao.topico || questao.disciplina}</span>
            <button onClick={() => { setQuestao(null); setResultado(null); setResposta(null) }}
                    className="text-sm text-[var(--color-text-light)]">fechar</button>
          </div>
          <p className="mb-4 leading-relaxed">{questao.enunciado}</p>
          <div className="space-y-2">
            {questao.alternativas.map(alt => {
              let cls = 'border-[var(--color-border)] hover:border-primary-500'
              if (resultado) {
                if (alt.letra === resultado.resposta_correta) cls = 'border-success-500 bg-green-50'
                else if (alt.letra === resposta) cls = 'border-danger-500 bg-red-50'
              } else if (resposta === alt.letra) cls = 'border-primary-800 bg-primary-50'
              return (
                <button key={alt.letra} disabled={!!resultado} onClick={() => setResposta(alt.letra)}
                        className={`w-full text-left p-3 border-2 rounded-lg text-sm ${cls}`}>
                  <span className="font-bold mr-2">{alt.letra})</span>{alt.texto}
                </button>
              )
            })}
          </div>
          {!resultado ? (
            <button onClick={confirmar} disabled={!resposta || enviando}
                    className="btn-primary w-full mt-4 disabled:opacity-50 flex items-center justify-center gap-2">
              {enviando && <Loader2 className="w-4 h-4 animate-spin" />} Confirmar
            </button>
          ) : (
            <div className="mt-4 space-y-2">
              <p className={`font-bold ${resultado.correta ? 'text-success-500' : 'text-danger-500'}`}>
                {resultado.correta ? 'Correto!' : `Incorreto — gabarito ${resultado.resposta_correta}`}
              </p>
              <p className="text-sm bg-[var(--color-bg)] p-3 rounded">{resultado.explicacao}</p>
              <p className="text-xs text-[var(--color-text-light)] flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> {resultado.explicacao_ia.estrategia}
              </p>
              <p className="text-xs text-[var(--color-text-light)]">
                Próxima revisão em {resultado.intervalo_dias} dia(s) — {dataBR(resultado.proxima_revisao)}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
