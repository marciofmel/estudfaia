import { useState } from 'react'
import { ChevronLeft, Check, X, Clock, BarChart3 } from 'lucide-react'

export function Questoes() {
  const [resposta, setResposta] = useState<string | null>(null)
  const [mostrou, setMostrou] = useState(false)

  const questao = {
    enunciado: 'Assinale a alternativa em que a concordância verbal está INCORRETA:',
    alternativas: [
      { letra: 'A', texto: 'Havia muitas pessoas na sala.' },
      { letra: 'B', texto: 'Fazem dois anos que não chove.' },
      { letra: 'C', texto: 'Os alunos e o professor chegaram.' },
      { letra: 'D', texto: 'A maioria dos alunos passou.' },
    ],
    resposta_correta: 'B',
    explicacao: 'O verbo "fazer" (tempo decorrido) é impessoal e deve ficar no singular: "Faz dois anos que não chove." Regra: verbos impessoais (haver, fazer) usados para tempo decorrido ficam no singular.',
    estatistica: 62.5,
    disciplina: 'Português',
    banca: 'Cebraspe',
    ano: 2024,
  }

  const confirmar = () => {
    if (resposta) setMostrou(true)
  }

  const correta = resposta === questao.resposta_correta

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button className="flex items-center gap-1 text-[var(--color-text-light)] hover:text-primary-800">
          <ChevronLeft className="w-5 h-5" /> Voltar
        </button>
        <div className="text-center">
          <span className="text-sm text-[var(--color-text-light)]">{questao.disciplina} — {questao.banca} {questao.ano}</span>
          <div className="text-sm font-medium">Questão 15 de 30</div>
        </div>
        <div className="flex items-center gap-1 text-[var(--color-text-light)]">
          <Clock className="w-4 h-4" /> 01:23
        </div>
      </div>

      {/* Progress */}
      <div className="w-full bg-gray-200 rounded-full h-1.5">
        <div className="bg-primary-800 h-1.5 rounded-full" style={{ width: '50%' }} />
      </div>

      {/* Questão */}
      <div className="card">
        <p className="text-lg mb-6 leading-relaxed">{questao.enunciado}</p>

        <div className="space-y-3">
          {questao.alternativas.map(alt => {
            let cls = 'border-[var(--color-border)] hover:border-primary-500'
            if (mostrou) {
              if (alt.letra === questao.resposta_correta) cls = 'border-success-500 bg-green-50'
              else if (alt.letra === resposta) cls = 'border-danger-500 bg-red-50'
            } else if (resposta === alt.letra) {
              cls = 'border-primary-800 bg-primary-50'
            }
            return (
              <button
                key={alt.letra}
                onClick={() => !mostrou && setResposta(alt.letra)}
                className={`w-full text-left p-4 border-2 rounded-lg transition-all ${cls}`}
                disabled={mostrou}
              >
                <span className="font-bold mr-3">{alt.letra})</span>
                {alt.texto}
                {mostrou && alt.letra === questao.resposta_correta && <Check className="inline w-5 h-5 text-success-500 ml-2" />}
                {mostrou && alt.letra === resposta && alt.letra !== questao.resposta_correta && <X className="inline w-5 h-5 text-danger-500 ml-2" />}
              </button>
            )
          })}
        </div>

        {!mostrou && (
          <button onClick={confirmar} disabled={!resposta} className="btn-primary w-full mt-6 disabled:opacity-50 disabled:cursor-not-allowed">
            Confirmar Resposta
          </button>
        )}
      </div>

      {/* Resultado */}
      {mostrou && (
        <div className={`card ${correta ? 'border-success-500' : 'border-danger-500'}`}>
          <div className="flex items-center gap-2 mb-3">
            {correta ? <Check className="w-6 h-6 text-success-500" /> : <X className="w-6 h-6 text-danger-500" />}
            <span className={`font-bold text-lg ${correta ? 'text-success-500' : 'text-danger-500'}`}>
              {correta ? 'Correto!' : 'Incorreto'}
            </span>
            <span className="text-sm text-[var(--color-text-light)] ml-auto">
              Resposta correta: {questao.resposta_correta}
            </span>
          </div>
          <div className="bg-[var(--color-bg)] p-4 rounded-lg mb-3">
            <p className="font-medium mb-2">📝 Explicação:</p>
            <p className="text-sm leading-relaxed">{questao.explicacao}</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-[var(--color-text-light)]">
            <BarChart3 className="w-4 h-4" />
            {questao.estatistica}% dos alunos acertaram esta questão
          </div>
          <div className="flex gap-3 mt-4">
            <button className="btn-primary flex-1">Próxima Questão →</button>
            <button className="btn-secondary">Caderno de Erros</button>
          </div>
        </div>
      )}
    </div>
  )
}
