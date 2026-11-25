import { useEffect, useRef, useState } from 'react'
import {
  Phone, Bell, Shield, CreditCard, LogOut, Check, QrCode, Loader2,
  RefreshCw, Send, AlertTriangle, Unlink, MessageSquare, Copy
} from 'lucide-react'
import { api } from '../lib/api'

type Sessao = { estado: string; conectado: boolean; telefone?: string | null }
type Diag = {
  evolution_online: boolean
  url: string
  instancia: string
  instrucoes?: { como_subir: string; url_esperada: string; teste: string } | null
}
type Prefs = { areas: string[]; regioes: string[]; salario_min: number; notificacoes: Record<string, boolean> }

const AREAS = ['Policial', 'Tribunal', 'Administrativo', 'Bancário', 'Previdenciário', 'Fiscal']
const REGIOES = ['MS', 'SP', 'RJ', 'MG', 'Nacional']

export function Perfil() {
  const [usuario, setUsuario] = useState<any>(null)
  const [diag, setDiag] = useState<Diag | null>(null)
  const [sessao, setSessao] = useState<Sessao>({ estado: 'desconectado', conectado: false })
  const [qr, setQr] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [prefs, setPrefs] = useState<Prefs>({ areas: [], regioes: [], salario_min: 0, notificacoes: {} })
  const [msgs, setMsgs] = useState<any[]>([])
  const pollRef = useRef<number | null>(null)

  useEffect(() => {
    api('/api/auth/me').then(setUsuario).catch(() => setUsuario({ nome: 'Aluno Demo', email: 'demo@concursosai.com.br', plano: 'pro' }))
    api<Prefs>('/api/perfil/preferencias').then(setPrefs).catch(() => {})
    api<any[]>('/api/whatsapp/mensagens').then(setMsgs).catch(() => {})
    consultarEstado()
    return () => { if (pollRef.current) window.clearInterval(pollRef.current) }
  }, [])

  async function consultarEstado() {
    try {
      const d = await api<Diag>('/api/whatsapp/diagnostico')
      setDiag(d)
      const s = await api<Sessao>('/api/whatsapp/estado')
      setSessao(s)
      if (s.conectado) { setQr(null); pararPoll() }
    } catch (e: any) {
      setErro(e.message)
    }
  }

  function pararPoll() {
    if (pollRef.current) { window.clearInterval(pollRef.current); pollRef.current = null }
  }

  function iniciarPoll() {
    pararPoll()
    let tentativas = 0
    pollRef.current = window.setInterval(async () => {
      tentativas++
      try {
        const s = await api<Sessao>('/api/whatsapp/estado')
        setSessao(s)
        if (s.conectado) {
          pararPoll(); setQr(null)
          setAviso('WhatsApp conectado com sucesso! Envie a mensagem de teste.')
          api<any[]>('/api/whatsapp/mensagens').then(setMsgs).catch(() => {})
        }
      } catch { /* segue tentando */ }
      if (tentativas > 45) pararPoll()
    }, 4000)
  }

  async function conectar() {
    setErro(null); setAviso(null); setCarregando(true); setQr(null)
    try {
      const r = await api<any>('/api/whatsapp/conectar', { method: 'POST', body: {} })
      if (r.conectado) {
        setSessao({ estado: 'open', conectado: true, telefone: r.telefone })
        setAviso('WhatsApp já estava conectado.')
      } else if (r.qrcode) {
        setQr(r.qrcode)
        setSessao({ estado: 'aguardando_qr', conectado: false })
        iniciarPoll()
      }
    } catch (e: any) {
      setErro(e.message)
      consultarEstado()
    } finally {
      setCarregando(false)
    }
  }

  async function atualizarQr() {
    setErro(null)
    try {
      const r = await api<any>('/api/whatsapp/qrcode')
      setQr(r.qrcode)
    } catch (e: any) { setErro(e.message) }
  }

  async function desconectar() {
    setCarregando(true); setErro(null)
    try {
      await api('/api/whatsapp/desconectar', { method: 'POST', body: {} })
      setSessao({ estado: 'desconectado', conectado: false })
      setQr(null); setAviso('WhatsApp desconectado.')
      pararPoll()
    } catch (e: any) { setErro(e.message) }
    finally { setCarregando(false) }
  }

  async function enviarTeste() {
    setCarregando(true); setErro(null); setAviso(null)
    try {
      const r = await api<any>('/api/whatsapp/teste', { method: 'POST', body: {} })
      setAviso(`Mensagem enviada para ${r.telefone}. Confira no seu WhatsApp.`)
      api<any[]>('/api/whatsapp/mensagens').then(setMsgs).catch(() => {})
    } catch (e: any) { setErro(e.message) }
    finally { setCarregando(false) }
  }

  async function salvarPrefs() {
    setCarregando(true); setErro(null)
    try {
      await api('/api/perfil/preferencias', { method: 'PUT', body: prefs })
      setAviso('Preferências salvas.')
    } catch (e: any) { setErro(e.message) }
    finally { setCarregando(false) }
  }

  function toggleArea(a: string) {
    setPrefs(p => ({ ...p, areas: p.areas.includes(a) ? p.areas.filter(x => x !== a) : [...p.areas, a] }))
  }
  function toggleRegiao(r: string) {
    setPrefs(p => ({ ...p, regioes: p.regioes.includes(r) ? p.regioes.filter(x => x !== r) : [...p.regioes, r] }))
  }
  function toggleNotif(chave: string) {
    setPrefs(p => ({ ...p, notificacoes: { ...p.notificacoes, [chave]: !p.notificacoes[chave] } }))
  }

  const conectado = sessao.conectado

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">👤 Meu Perfil</h1>

      {(erro || aviso) && (
        <div className={`card flex items-start gap-3 ${erro ? 'border-danger-500' : 'border-success-500'}`}>
          {erro ? <AlertTriangle className="w-5 h-5 text-danger-500 shrink-0 mt-0.5" />
               : <Check className="w-5 h-5 text-success-500 shrink-0 mt-0.5" />}
          <div className="text-sm flex-1">
            <p className={erro ? 'text-danger-500' : 'text-success-500'}>{erro || aviso}</p>
            {erro && diag && !diag.evolution_online && diag.instrucoes && (
              <div className="mt-2 p-3 bg-[var(--color-bg)] rounded-lg text-[var(--color-text-light)]">
                <p className="font-medium text-[var(--color-text)] mb-1">Como ligar o WhatsApp (Evolution API):</p>
                <p>1. Abra o Docker Desktop</p>
                <p>2. No terminal, na pasta do projeto: <code className="font-mono">{diag.instrucoes.como_subir}</code></p>
                <p>3. Aguarde ~30s e clique em "Conectar WhatsApp" novamente</p>
                <p className="mt-1 text-xs">Instância: {diag.instancia} • {diag.url}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Info do usuário */}
      <div className="card flex items-center gap-4">
        <div className="w-16 h-16 bg-primary-800 rounded-full flex items-center justify-center text-white text-2xl font-bold">
          {(usuario?.nome || 'A')[0]}
        </div>
        <div>
          <h2 className="font-bold text-lg">{usuario?.nome || 'Aluno Demo'}</h2>
          <p className="text-[var(--color-text-light)]">{usuario?.email}</p>
          <span className="badge bg-primary-100 text-primary-800 mt-1">
            Plano {(usuario?.plano || 'pro').toUpperCase()}
          </span>
        </div>
      </div>

      {/* WhatsApp — fluxo REAL com QR */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-lg flex items-center gap-2">
            <Phone className="w-5 h-5 text-success-500" /> WhatsApp
          </h2>
          <span className={`badge ${conectado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
            {conectado ? 'Conectado' : 'Desconectado'}
          </span>
        </div>

        {conectado ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-success-500" />
              <span className="font-medium">{sessao.telefone || 'número conectado'}</span>
              <span className="badge bg-green-100 text-green-700">Ativo</span>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Notificações:</p>
              {[
                ['editais', 'Novos editais compatíveis'],
                ['revisao', 'Lembrete de revisão diária'],
                ['prazos', 'Alertas de prazo de inscrição'],
                ['cronograma', 'Cronograma atualizado'],
              ].map(([chave, label]) => (
                <label key={chave} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="rounded"
                         checked={prefs.notificacoes?.[chave] ?? true}
                         onChange={() => toggleNotif(chave)} />
                  {label}
                </label>
              ))}
            </div>
            <div className="flex flex-wrap gap-2 pt-1">
              <button onClick={enviarTeste} disabled={carregando}
                      className="btn-primary text-sm flex items-center gap-2">
                {carregando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Enviar mensagem de teste
              </button>
              <button onClick={consultarEstado} className="btn-secondary text-sm flex items-center gap-2">
                <RefreshCw className="w-4 h-4" /> Atualizar status
              </button>
              <button onClick={desconectar} disabled={carregando}
                      className="btn-secondary text-sm flex items-center gap-2 text-danger-500">
                <Unlink className="w-4 h-4" /> Desconectar
              </button>
            </div>
            <p className="text-xs text-[var(--color-text-light)]">
              Envie <b>status</b>, <b>revisoes</b>, <b>simulados</b> ou <b>editais</b> pelo WhatsApp para receber seus dados reais.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-[var(--color-text-light)]">
              Conecte o seu WhatsApp (número pessoal) escaneando o QR Code. Depois disso a plataforma
              envia notificações e responde comandos por lá.
            </p>

            {qr ? (
              <div className="flex flex-col items-center gap-3 p-4 bg-white rounded-lg border border-[var(--color-border)]">
                <img src={qr.startsWith('data:') ? qr : `data:image/png;base64,${qr}`}
                     alt="QR Code do WhatsApp" className="w-56 h-56 object-contain" />
                <p className="text-sm text-center text-gray-600">
                  WhatsApp → <b>Dispositivos conectados</b> → Conectar dispositivo
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Loader2 className="w-3 h-3 animate-spin" /> aguardando leitura do QR…
                </div>
                <button onClick={atualizarQr} className="btn-secondary text-xs flex items-center gap-1">
                  <RefreshCw className="w-3 h-3" /> Gerar novo QR
                </button>
              </div>
            ) : (
              <button onClick={conectar} disabled={carregando}
                      className="btn-primary w-full flex items-center justify-center gap-2">
                {carregando ? <Loader2 className="w-5 h-5 animate-spin" /> : <QrCode className="w-5 h-5" />}
                {carregando ? 'Gerando QR Code…' : 'Conectar WhatsApp'}
              </button>
            )}

            {diag && (
              <p className="text-xs text-[var(--color-text-light)]">
                Evolution API: {diag.evolution_online ? '🟢 online' : '🔴 offline'} • instância {diag.instancia}
              </p>
            )}
          </div>
        )}

        {msgs.length > 0 && (
          <div className="mt-5 pt-4 border-t border-[var(--color-border)]">
            <p className="text-sm font-medium flex items-center gap-2 mb-2">
              <MessageSquare className="w-4 h-4" /> Últimas mensagens
            </p>
            <div className="space-y-1 max-h-40 overflow-auto">
              {msgs.slice(0, 6).map((m, i) => (
                <div key={i} className="text-xs p-2 bg-[var(--color-bg)] rounded flex justify-between gap-2">
                  <span className="line-clamp-2">{m.texto}</span>
                  <span className="text-[var(--color-text-light)] shrink-0">{m.criado_em?.slice(11, 16)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Preferências */}
      <div className="card">
        <h2 className="font-bold text-lg flex items-center gap-2 mb-4">
          <Bell className="w-5 h-5 text-primary-800" /> Preferências de Busca
        </h2>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Áreas de interesse</label>
            <div className="flex gap-2 flex-wrap">
              {AREAS.map(a => {
                const ativo = prefs.areas?.includes(a)
                return (
                  <button key={a} onClick={() => toggleArea(a)}
                    className={`badge cursor-pointer ${ativo ? 'bg-primary-800 text-white' : 'bg-primary-100 text-primary-800'}`}>
                    {a} {ativo ? '✓' : '+'}
                  </button>
                )
              })}
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Regiões</label>
            <div className="flex gap-2 flex-wrap">
              {REGIOES.map(r => {
                const ativo = prefs.regioes?.includes(r)
                return (
                  <button key={r} onClick={() => toggleRegiao(r)}
                    className={`badge cursor-pointer ${ativo ? 'bg-primary-800 text-white' : 'bg-primary-100 text-primary-800'}`}>
                    {r} {ativo ? '✓' : '+'}
                  </button>
                )
              })}
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Salário mínimo desejado</label>
            <input className="input" type="number" value={prefs.salario_min || 0}
                   onChange={e => setPrefs(p => ({ ...p, salario_min: Number(e.target.value) }))} />
          </div>
          <button onClick={salvarPrefs} disabled={carregando} className="btn-primary w-full">
            Salvar Preferências
          </button>
        </div>
      </div>

      {/* Conta */}
      <div className="card">
        <h2 className="font-bold text-lg flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-primary-800" /> Conta
        </h2>
        <div className="space-y-2">
          <button className="flex items-center gap-2 text-sm text-[var(--color-text-light)] hover:text-primary-800 w-full p-2 rounded-lg hover:bg-primary-50">
            <CreditCard className="w-4 h-4" /> Gerenciar assinatura
          </button>
          <button
            onClick={() => { localStorage.removeItem('concursosai_token'); window.location.href = '/login' }}
            className="flex items-center gap-2 text-sm text-danger-500 hover:text-danger-600 w-full p-2 rounded-lg hover:bg-red-50">
            <LogOut className="w-4 h-4" /> Sair
          </button>
        </div>
      </div>
    </div>
  )
}
