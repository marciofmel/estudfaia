import { useState } from 'react'
import { Phone, Bell, Shield, CreditCard, LogOut, Check } from 'lucide-react'

export function Perfil() {
  const [whatsappVinculado] = useState(true)

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">👤 Meu Perfil</h1>

      {/* Info do usuário */}
      <div className="card flex items-center gap-4">
        <div className="w-16 h-16 bg-primary-800 rounded-full flex items-center justify-center text-white text-2xl font-bold">J</div>
        <div>
          <h2 className="font-bold text-lg">João Silva</h2>
          <p className="text-[var(--color-text-light)]">joao@email.com</p>
          <span className="badge bg-primary-100 text-primary-800 mt-1">Plano Pro — R$ 49,90/mês</span>
        </div>
      </div>

      {/* WhatsApp */}
      <div className="card">
        <h2 className="font-bold text-lg flex items-center gap-2 mb-4">
          <Phone className="w-5 h-5 text-success-500" /> WhatsApp
        </h2>
        {whatsappVinculado ? (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Check className="w-5 h-5 text-success-500" />
              <span className="font-medium">+55 (67) 99999-9999</span>
              <span className="badge bg-green-100 text-green-700">Verificado</span>
            </div>
            <div className="space-y-2 mb-4">
              <p className="text-sm font-medium">Notificações:</p>
              {['Novos editais compatíveis', 'Lembrete de revisão diária', 'Alertas de prazo de inscrição', 'Cronograma criado'].map(n => (
                <label key={n} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" defaultChecked className="rounded" /> {n}
                </label>
              ))}
            </div>
            <button className="btn-secondary text-sm">Desvincular WhatsApp</button>
          </div>
        ) : (
          <div>
            <p className="text-sm text-[var(--color-text-light)] mb-3">Vincule seu WhatsApp para receber notificações.</p>
            <input className="input mb-3" placeholder="+55 (__) _____-____" />
            <button className="btn-primary">Enviar código de verificação</button>
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
              {['Policial', 'Tribunal', 'Administrativo'].map(a => (
                <span key={a} className="badge bg-primary-100 text-primary-800">{a} ×</span>
              ))}
              <button className="badge bg-gray-100 text-gray-600 cursor-pointer">+ Adicionar</button>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Regiões</label>
            <div className="flex gap-2 flex-wrap">
              {['MS', 'SP', 'Nacional'].map(r => (
                <span key={r} className="badge bg-primary-100 text-primary-800">{r} ×</span>
              ))}
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Salário mínimo</label>
            <input className="input" type="number" defaultValue={4000} />
          </div>
          <button className="btn-primary w-full">Salvar Preferências</button>
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
          <button className="flex items-center gap-2 text-sm text-danger-500 hover:text-danger-600 w-full p-2 rounded-lg hover:bg-red-50">
            <LogOut className="w-4 h-4" /> Sair
          </button>
        </div>
      </div>
    </div>
  )
}
