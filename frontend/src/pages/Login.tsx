import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, Loader2, AlertTriangle } from 'lucide-react'
import { api, setToken } from '../lib/api'

export function Login() {
  const [modo, setModo] = useState<'login' | 'registro'>('login')
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('demo@concursosai.com.br')
  const [senha, setSenha] = useState('demo1234')
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)
  const navigate = useNavigate()

  async function entrar(e: React.FormEvent) {
    e.preventDefault()
    setErro(''); setCarregando(true)
    try {
      const rota = modo === 'login' ? '/api/auth/login' : '/api/auth/registro'
      const corpo = modo === 'login' ? { email, senha } : { nome, email, senha }
      const dados = await api<{ access_token: string }>(rota, { method: 'POST', body: corpo })
      setToken(dados.access_token)
      navigate('/')
    } catch (err: any) {
      setErro(err.message)
    } finally {
      setCarregando(false)
    }
  }

  async function entrarDemo() {
    setErro(''); setCarregando(true)
    try {
      const dados = await api<{ access_token: string }>('/api/auth/demo', { method: 'POST', body: {} })
      setToken(dados.access_token)
      navigate('/')
    } catch (err: any) {
      setErro(err.message)
    } finally { setCarregando(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[var(--color-bg)]">
      <div className="card w-full max-w-md">
        <div className="flex items-center gap-2 mb-6 justify-center">
          <div className="w-10 h-10 bg-primary-800 rounded-xl flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <span className="font-bold text-xl">ConcursosAI</span>
        </div>

        <h1 className="text-lg font-bold mb-1 text-center">
          {modo === 'login' ? 'Entrar na plataforma' : 'Criar sua conta'}
        </h1>
        <p className="text-sm text-[var(--color-text-light)] text-center mb-5">
          Estude com IA e receba editais no WhatsApp
        </p>

        {erro && (
          <div className="mb-4 p-3 bg-red-50 text-danger-500 rounded-lg text-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" /> {erro}
          </div>
        )}

        <form onSubmit={entrar} className="space-y-3">
          {modo === 'registro' && (
            <div>
              <label className="text-sm font-medium mb-1 block">Nome</label>
              <input className="input" value={nome} onChange={e => setNome(e.target.value)} required />
            </div>
          )}
          <div>
            <label className="text-sm font-medium mb-1 block">E-mail</label>
            <input className="input" type="email" value={email}
                   onChange={e => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Senha</label>
            <input className="input" type="password" value={senha}
                   onChange={e => setSenha(e.target.value)} required minLength={6} />
          </div>
          <button type="submit" disabled={carregando}
                  className="btn-primary w-full flex items-center justify-center gap-2">
            {carregando && <Loader2 className="w-4 h-4 animate-spin" />}
            {modo === 'login' ? 'Entrar' : 'Criar conta'}
          </button>
        </form>

        <button onClick={entrarDemo} disabled={carregando}
                className="btn-secondary w-full mt-2 text-sm">
          Entrar com conta demo
        </button>

        <p className="text-sm text-center mt-4 text-[var(--color-text-light)]">
          {modo === 'login' ? 'Não tem conta?' : 'Já tem conta?'}{' '}
          <button onClick={() => { setModo(modo === 'login' ? 'registro' : 'login'); setErro('') }}
                  className="text-primary-800 font-medium hover:underline">
            {modo === 'login' ? 'Cadastre-se' : 'Entrar'}
          </button>
        </p>
      </div>
    </div>
  )
}
