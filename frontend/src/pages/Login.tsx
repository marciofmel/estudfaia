import { useState } from 'react'
import { Zap, Mail, Lock, Eye, EyeOff } from 'lucide-react'

export function Login() {
  const [showPass, setShowPass] = useState(false)
  const [isLogin, setIsLogin] = useState(true)

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)] p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold">ConcursosAI</h1>
          <p className="text-[var(--color-text-light)]">Estude para concursos com IA</p>
        </div>

        <div className="card">
          <div className="flex mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 text-center font-medium rounded-lg transition-all ${isLogin ? 'bg-primary-800 text-white' : 'text-[var(--color-text-light)]'}`}
            >Entrar</button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 text-center font-medium rounded-lg transition-all ${!isLogin ? 'bg-primary-800 text-white' : 'text-[var(--color-text-light)]'}`}
            >Criar conta</button>
          </div>

          <div className="space-y-4">
            {!isLogin && (
              <div>
                <label className="text-sm font-medium mb-1 block">Nome</label>
                <input className="input" placeholder="Seu nome completo" />
              </div>
            )}
            <div>
              <label className="text-sm font-medium mb-1 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-light)]" />
                <input className="input pl-10" type="email" placeholder="seu@email.com" />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Senha</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-light)]" />
                <input className="input pl-10 pr-10" type={showPass ? 'text' : 'password'} placeholder="••••••••" />
                <button onClick={() => setShowPass(!showPass)} className="absolute right-3 top-1/2 -translate-y-1/2">
                  {showPass ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
            {!isLogin && (
              <div>
                <label className="text-sm font-medium mb-1 block">Telefone (WhatsApp)</label>
                <input className="input" placeholder="+55 (__) _____-____" />
              </div>
            )}
            <button className="btn-primary w-full">
              {isLogin ? 'Entrar' : 'Criar conta'}
            </button>
            {isLogin && (
              <p className="text-center text-sm text-[var(--color-text-light)]">
                <a href="#" className="text-primary-800 hover:underline">Esqueceu a senha?</a>
              </p>
            )}
          </div>
        </div>

        <p className="text-center text-xs text-[var(--color-text-light)] mt-6">
          Ao criar conta, você concorda com os Termos de Uso e Política de Privacidade.
        </p>
      </div>
    </div>
  )
}
