import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Target, TrendingUp, Search, Calendar, Sparkles, Loader2, AlertTriangle, Flame
} from 'lucide-react'
import { api, brl, dataBR } from '../lib/api'

type Resumo = {
  usuario: { nome: string; plano: string }
  respondidas: number; acertos: number; taxa_acerto: number
  revisoes_hoje: number; editais_novos: number
}
type Desempenho = {
  total: number; taxa_acerto: number; por_disciplina: any[]
  pontos_fracos: string[]; recomendacoes: string[]
  previsao_nota: { estimativa: number; faixa: number[] } | null
}
type Plano = { plano?: { semana: number; dias: any[] }[]; data_prova?: string; dias_restantes?: number }

export function Dashboard() {
  const [resumo, setResumo] = useState<Resumo | null>(null)
  const [desempenho, setDesempenho] = useState<Desempenho | null>(null)
  const [cronograma, setCronograma] = useState<Plano | null>(null)
  const [editais, setEditais] = useState<any[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    (async () => {
      try {
        const [r, d, c, e] = await Promise.all([
          api<Resumo>('/api/perfil/resumo'),
          api<Desempenho>('/api/ia/desempenho'),
          api<Plano>('/api/cronograma'),
          api<any[]>('/api/editais/novos'),
        ])
        setResumo(r); setDesempenho(d); setCronograma(c); setEditais(e.slice(0, 3))
      } catch (e: any) { setErro(e.message) }
      finally { setCarregando(false) }
    })()
  }, [])

  const hoje = new Date().toISOString().slice(0, 10)
  const dias = cronograma?.plano?.flatMap(s => s.dias) || []
  const atividadesHoje = dias.find(d => d.data === hoje)?.atividades
    || dias[0]?.atividades || []

  const hora = new Date().getHours()
  const saudacao = hora < 12 ? 'Bom dia' : hora < 18 ? 'Boa tarde' : 'Boa noite'
  const primeiroNome = (resumo?.usuario?.nome || 'Aluno').split(' ')[0]

  if (carregando) {
    return <div className="card flex justify-center py-20"><Loader2 className="w-7 h-7 animate-spin" /></div>
  }

  return (
    <div className="space-y-5">
      {erro && <div className="card border-danger-500 flex items-center gap-2 text-danger-500">
        <AlertTriangle className="w-5 h-5" /> {erro}</div>}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{saudacao}, {primeiroNome}! 👋</h1>
          <p className="text-[var(--color-text-light)]">
            {resumo?.revisoes_hoje
              ? `Você tem ${resumo.revisoes_hoje} revisões pendentes hoje.`
              : 'Nenhuma revisão pendente — bom momento para praticar.'}
          </p>
        </div>
        <div className="flex items-center gap-2 bg-amber-50 text-amber-700 px-4 py-2 rounded-lg">
          <Flame className="w-5 h-5" />
          <span className="font-bold">{resumo?.respondidas ?? 0}</span>
          <span className="text-sm">questões respondidas</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Desempenho */}
        <div className="card">
          <h2 className="font-bold text-lg flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-success-500" /> Seu desempenho
          </h2>
          <div className="flex items-center justify-center mb-3">
            <div className="relative w-32 h-32">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#E2E8F0" strokeWidth="8" />
                <circle cx="50" cy="50" r="40" fill="none" stroke="#10B981" strokeWidth="8"
                  strokeDasharray={`${(resumo?.taxa_acerto ?? 0) * 2.51} ${100 * 2.51}`}
                  strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold">{resumo?.taxa_acerto ?? 0}%</span>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div><p className="text-xl font-bold text-success-500">{resumo?.acertos ?? 0}</p>
              <p className="text-xs text-[var(--color-text-light)]">Acertos</p></div>
            <div><p className="text-xl font-bold text-danger-500">
              {(resumo?.respondidas ?? 0) - (resumo?.acertos ?? 0)}</p>
              <p className="text-xs text-[var(--color-text-light)]">Erros</p></div>
            <div><p className="text-xl font-bold text-primary-800">{resumo?.respondidas ?? 0}</p>
              <p className="text-xs text-[var(--color-text-light)]">Total</p></div>
          </div>
          {desempenho?.previsao_nota && (
            <p className="text-xs text-center text-[var(--color-text-light)] mt-3">
              Previsão de nota: {desempenho.previsao_nota.faixa[0]}–{desempenho.previsao_nota.faixa[1]} pontos
            </p>
          )}
        </div>

        {/* Concursos */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-lg flex items-center gap-2">
              <Target className="w-5 h-5 text-primary-800" /> Foco atual
            </h2>
            <Link to="/descobrir" className="text-sm text-primary-800 hover:underline">+ Adicionar</Link>
          </div>
          <div className="space-y-3">
            {desempenho?.por_disciplina?.slice(0, 4).map(d => (
              <div key={d.disciplina} className="p-3 bg-[var(--color-bg)] rounded-lg">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-sm">{d.disciplina}</span>
                  <span className="text-xs text-[var(--color-text-light)]">{d.taxa_acerto}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-primary-800 h-2 rounded-full" style={{ width: `${d.taxa_acerto}%` }} />
                </div>
              </div>
            ))}
            {!desempenho?.por_disciplina?.length && (
              <p className="text-sm text-[var(--color-text-light)]">
                Responda questões para ver seu progresso por disciplina.
              </p>
            )}
          </div>
          {cronograma?.dias_restantes != null && (
            <p className="text-xs text-[var(--color-text-light)] mt-3">
              Prova em {cronograma.dias_restantes} dias ({dataBR(cronograma.data_prova)})
            </p>
          )}
        </div>
      </div>

      {/* IA recomendações */}
      {desempenho && desempenho.recomendacoes?.length > 0 && (
        <div className="card">
          <h2 className="font-bold text-lg flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-primary-800" /> Recomendações da IA
          </h2>
          <ul className="space-y-1 text-sm">
            {desempenho.recomendacoes.map((r, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-primary-800">•</span> {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Cronograma de hoje */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-lg flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary-800" /> Plano de hoje
          </h2>
          <Link to="/cronograma" className="text-sm text-primary-800 hover:underline">Ver cronograma</Link>
        </div>
        <div className="space-y-2">
          {atividadesHoje.map((a: any, i: number) => (
            <div key={i} className="flex items-center gap-3 p-3 bg-[var(--color-bg)] rounded-lg">
              <span className="flex-1 text-sm">
                <b>{a.disciplina}</b> — {a.topico}
              </span>
              <span className="text-xs text-[var(--color-text-light)]">{a.duracao_h}h</span>
              <span className={`badge ${a.tipo === 'revisao' ? 'bg-amber-100 text-amber-700'
                : a.tipo === 'simulado' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                {a.tipo}
              </span>
            </div>
          ))}
          {!atividadesHoje.length && (
            <p className="text-sm text-[var(--color-text-light)]">Gere seu cronograma para ver as atividades.</p>
          )}
        </div>
        <Link to="/questoes" className="btn-primary w-full mt-4 block text-center">Começar a estudar</Link>
      </div>

      {/* Editais */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-lg flex items-center gap-2">
            <Search className="w-5 h-5 text-primary-800" /> Novos editais
          </h2>
          <Link to="/descobrir" className="text-sm text-primary-800 hover:underline">Ver todos</Link>
        </div>
        <div className="space-y-2">
          {editais.map(e => (
            <div key={e.id} className="flex items-center justify-between p-3 bg-[var(--color-bg)] rounded-lg gap-2">
              <div className="min-w-0">
                <p className="font-medium text-sm truncate">{e.titulo}</p>
                <p className="text-xs text-[var(--color-text-light)]">
                  Prova: {dataBR(e.data_prova)} • {brl(e.salario)}
                </p>
              </div>
              <span className={`badge shrink-0 ${Number(e.score) >= 80 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                {e.score}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
