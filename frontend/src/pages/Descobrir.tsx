import { useEffect, useState } from 'react'
import {
  Check, X, Bookmark, Loader2, Sparkles, Radar, AlertTriangle, ExternalLink, CalendarDays
} from 'lucide-react'
import { api, brl, dataBR } from '../lib/api'

type Edital = {
  id: string; titulo: string; orgao?: string; banca?: string; cargo?: string
  salario?: number; data_prova?: string; url?: string; fonte?: string
  score?: number; status: string; area?: string; uf?: string
}
type Analise = {
  orgao?: string; banca?: string; cargo?: string; salario?: number; vagas?: number
  datas: { iso: string; br: string }[]
  disciplinas: { nome: string; peso_pct: number; topicos: string[] }[]
  resumo: string; confianca: number; estrutura_inferida: boolean
}

export function Descobrir() {
  const [editais, setEditais] = useState<Edital[]>([])
  const [passados, setPassados] = useState<Edital[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [monitorando, setMonitorando] = useState(false)
  const [texto, setTexto] = useState('')
  const [url, setUrl] = useState('')
  const [analise, setAnalise] = useState<Analise | null>(null)
  const [analisando, setAnalisando] = useState(false)

  useEffect(() => { carregar() }, [])

  async function carregar() {
    setCarregando(true)
    try {
      const [novos, antigos] = await Promise.all([
        api<Edital[]>('/api/editais/novos'),
        api<Edital[]>('/api/editais/passados'),
      ])
      setEditais(novos); setPassados(antigos)
    } catch (e: any) { setErro(e.message) }
    finally { setCarregando(false) }
  }

  async function monitorar() {
    setMonitorando(true); setErro(null); setAviso(null)
    try {
      const r = await api<any>('/api/editais/monitorar')
      setAviso(r.fonte_online
        ? `Monitoramento concluído: ${r.editais.length} editais lidos, ${r.gravados} novos gravados.`
        : `Portais externos não responderam (${(r.falhas || []).join(', ')}). Base local continua com ${r.total_base} editais.`)
      carregar()
    } catch (e: any) { setErro(e.message) }
    finally { setMonitorando(false) }
  }

  async function responder(id: string, resposta: string) {
    try {
      await api(`/api/editais/${id}/responder`, { method: 'POST', body: { resposta } })
      if (resposta === 'descartar') setEditais(prev => prev.filter(e => e.id !== id))
      else setAviso('Interesse registrado! Você receberá alertas no WhatsApp.')
    } catch (e: any) { setErro(e.message) }
  }

  async function analisar() {
    setAnalisando(true); setErro(null); setAnalise(null)
    try {
      const r = await api<Analise>('/api/ia/analisar-edital', {
        method: 'POST',
        body: { texto: texto || undefined, url: url || undefined },
        timeout: 60000,
      })
      setAnalise(r)
    } catch (e: any) { setErro(e.message) }
    finally { setAnalisando(false) }
  }

  async function gerarCronograma() {
    if (!analise) return
    setAnalisando(true)
    try {
      await api('/api/ia/cronograma', {
        method: 'POST',
        body: {
          disciplinas: analise.disciplinas.map(d => ({ nome: d.nome, peso: d.peso_pct, topicos: d.topicos })),
          data_prova: analise.datas?.[0]?.iso,
          horas_dia: 3,
        },
      })
      setAviso('Cronograma gerado pela IA! Veja em "Cronograma".')
    } catch (e: any) { setErro(e.message) }
    finally { setAnalisando(false) }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">🔍 Descobrir Concursos</h1>
          <p className="text-sm text-[var(--color-text-light)]">
            {editais.length} editais abertos • {passados.length} editais anteriores
          </p>
        </div>
        <button onClick={monitorar} disabled={monitorando} className="btn-secondary flex items-center gap-2">
          {monitorando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Radar className="w-4 h-4" />}
          {monitorando ? 'Varrendo portais…' : 'Monitorar novos editais'}
        </button>
      </div>

      {erro && <div className="card border-danger-500 flex items-center gap-2 text-danger-500">
        <AlertTriangle className="w-5 h-5" /> {erro}</div>}
      {aviso && <div className="card border-success-500 flex items-center gap-2 text-success-500">
        <Check className="w-5 h-5" /> {aviso}</div>}

      {/* IA — analisador de edital */}
      <div className="card">
        <h2 className="font-bold text-lg flex items-center gap-2 mb-1">
          <Sparkles className="w-5 h-5 text-primary-800" /> IA — Ler edital e montar plano
        </h2>
        <p className="text-sm text-[var(--color-text-light)] mb-3">
          Cole o texto do edital ou a URL. A IA extrai órgão, banca, salário, vagas, datas e a
          estrutura de disciplinas com peso — e gera seu cronograma.
        </p>
        <div className="space-y-2">
          <input className="input" placeholder="URL do edital (opcional)"
                 value={url} onChange={e => setUrl(e.target.value)} />
          <textarea className="input h-28" placeholder="Ou cole aqui o texto do edital…"
                    value={texto} onChange={e => setTexto(e.target.value)} />
          <button onClick={analisar} disabled={analisando || (!texto && !url)}
                  className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
            {analisando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {analisando ? 'Analisando com IA…' : 'Analisar edital com IA'}
          </button>
        </div>

        {analise && (
          <div className="mt-4 space-y-3 border-t border-[var(--color-border)] pt-4">
            <p className="text-sm">{analise.resumo}</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
              <div className="p-2 bg-[var(--color-bg)] rounded"><span className="text-xs text-[var(--color-text-light)] block">Órgão</span>{analise.orgao || '—'}</div>
              <div className="p-2 bg-[var(--color-bg)] rounded"><span className="text-xs text-[var(--color-text-light)] block">Banca</span>{analise.banca || '—'}</div>
              <div className="p-2 bg-[var(--color-bg)] rounded"><span className="text-xs text-[var(--color-text-light)] block">Salário</span>{brl(analise.salario)}</div>
              <div className="p-2 bg-[var(--color-bg)] rounded"><span className="text-xs text-[var(--color-text-light)] block">Vagas</span>{analise.vagas ?? '—'}</div>
            </div>
            <div>
              <p className="text-sm font-medium mb-1">Disciplinas detectadas</p>
              <div className="space-y-1">
                {analise.disciplinas.map(d => (
                  <div key={d.nome} className="flex items-center gap-2 text-sm">
                    <span className="w-40 shrink-0">{d.nome}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div className="bg-primary-800 h-2 rounded-full" style={{ width: `${Math.min(100, d.peso_pct * 2)}%` }} />
                    </div>
                    <span className="w-12 text-right text-[var(--color-text-light)]">{d.peso_pct}%</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex items-center justify-between text-xs text-[var(--color-text-light)]">
              <span>Confiança da leitura: {analise.confianca}%{analise.estrutura_inferida ? ' (estrutura estimada por área)' : ''}</span>
              <button onClick={gerarCronograma} disabled={analisando} className="btn-primary text-xs px-3 py-1.5">
                Gerar cronograma com a IA
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Novos Editais */}
      <div>
        <h2 className="font-bold text-lg mb-3">🆕 Editais abertos</h2>
        {carregando ? (
          <div className="card flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin" /></div>
        ) : (
          <div className="space-y-3">
            {editais.map(e => (
              <div key={e.id} className="card">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex-1">
                    <h3 className="font-bold">{e.titulo}</h3>
                    <p className="text-sm text-[var(--color-text-light)]">
                      {e.orgao} • {e.banca || 'banca a definir'}
                    </p>
                    <div className="flex flex-wrap gap-3 mt-1 text-sm">
                      <span className="flex items-center gap-1"><CalendarDays className="w-3.5 h-3.5" /> {dataBR(e.data_prova)}</span>
                      <span>💰 {brl(e.salario)}</span>
                      <span className={Number(e.score) >= 80 ? 'text-success-500 font-bold' : 'text-primary-800 font-bold'}>
                        🎯 {e.score ?? 0}% match
                      </span>
                      {e.fonte && <span className="text-[var(--color-text-light)] text-xs">{e.fonte}</span>}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => responder(e.id, 'interesse')}
                            className="btn-primary text-sm px-4 py-2 flex items-center gap-1">
                      <Check className="w-4 h-4" /> Interesse
                    </button>
                    <button onClick={() => responder(e.id, 'descartar')}
                            className="btn-secondary text-sm px-4 py-2 flex items-center gap-1">
                      <X className="w-4 h-4" /> Descartar
                    </button>
                    {e.url && (
                      <a href={e.url} target="_blank" rel="noreferrer"
                         className="p-2 hover:bg-gray-100 rounded-lg" title="Abrir fonte">
                        <ExternalLink className="w-5 h-5 text-[var(--color-text-light)]" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {editais.length === 0 && <p className="text-sm text-[var(--color-text-light)]">Nenhum edital aberto.</p>}
          </div>
        )}
      </div>

      {/* Editais Passados */}
      <div>
        <h2 className="font-bold text-lg mb-3">📚 Estudar com edital passado</h2>
        <div className="card space-y-2">
          {passados.map(e => (
            <div key={e.id} className="flex items-center justify-between p-3 bg-[var(--color-bg)] rounded-lg">
              <div>
                <p className="font-medium">{e.titulo}</p>
                <p className="text-sm text-[var(--color-text-light)]">
                  {e.banca} • prova {dataBR(e.data_prova)}
                </p>
              </div>
              <button onClick={() => responder(e.id, 'salvar')}
                      className="btn-secondary text-sm px-4 py-2 flex items-center gap-1">
                <Bookmark className="w-4 h-4" /> Usar como base
              </button>
            </div>
          ))}
          {passados.length === 0 && <p className="text-sm text-[var(--color-text-light)]">Sem editais anteriores cadastrados.</p>}
        </div>
      </div>
    </div>
  )
}
