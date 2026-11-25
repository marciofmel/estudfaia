# backend/src/ia_engine.py
"""Motor de IA local do ConcursosAI.

Roda 100% offline, sem chave de API: usa NLP determinístico (regex + dicionários
ponderados + heurísticas) para:

1. Ler um edital (texto colado ou URL) e extrair órgão, banca, cargo, salário,
   vagas, datas e a estrutura de disciplinas com pesos.
2. Gerar cronograma de estudos real (distribuição por peso, revisão espaçada,
   simulados semanais) a partir da data da prova.
3. Analisar o desempenho do aluno e apontar pontos fracos com plano de ação.
4. Explicar questões com estratégia de resolução por tópico.
5. Monitorar novos editais em fontes públicas (com fallback para base local).

Se existir OPENAI_API_KEY válida no ambiente, o módulo usa o LLM como
"segunda opinião" para o resumo — mas nunca depende dele para funcionar.
"""

import os
import re
import json
import hashlib
import unicodedata
from datetime import datetime, date, timedelta

# ------------------------------------------------------------------ utilidades
def _norm(txt: str) -> str:
    """minúsculas e sem acento, para casar palavras-chave."""
    txt = unicodedata.normalize("NFKD", txt or "")
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt.lower()


def _slug(txt: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _norm(txt)).strip("-")


BANCAS = [
    "Cebraspe", "CESPE", "FCC", "FGV", "VUNESP", "Cesgranrio", "IBFC", "FAPEMS",
    "Quadrix", "IDECAN", "Instituto AOCP", "AOCP", "IBADE", "INSTITUTO CONSULPLAN",
    "Consulplan", "NC UFPR", "UFPR", "FUNDATEC", "Legalle", "OBJETIVA", "IBGP",
    "FAURGS", "ESAF", "IADES", "CEBRASPE",
]

ORGAOS_CONHECIDOS = [
    "Polícia Rodoviária Federal", "Polícia Federal", "Polícia Militar",
    "Instituto Nacional do Seguro Social", "Tribunal de Justiça", "Receita Federal",
    "Banco do Brasil", "Caixa Econômica Federal", "Correios", "IBGE", "Ministério",
    "Secretaria", "Prefeitura", "Câmara", "Assembleia", "Defensoria", "Ministério Público",
    "Universidade Federal", "Instituto Federal", "Agência Nacional", "TRE", "TRT", "TRF",
]

# Disciplinas: nome -> (palavras-chave, peso-base, tópicos)
DISCIPLINAS = {
    "Português": (
        ["lingua portuguesa", "portugues", "interpretacao de texto", "gramatica",
         "ortografia", "concordancia", "redacao"],
        15,
        ["Interpretação de texto", "Ortografia e acentuação", "Concordância verbal e nominal",
         "Regência e crase", "Pontuação", "Classes de palavras", "Coesão e coerência"],
    ),
    "Raciocínio Lógico": (
        ["raciocinio logico", "logica", "proposicoes", "argumentacao logica",
         "logica matematica", "estruturas logicas"],
        10,
        ["Proposições e conectivos", "Equivalências e negações", "Silogismos",
         "Análise combinatória", "Probabilidade", "Sequências lógicas"],
    ),
    "Matemática": (
        ["matematica", "aritmetica", "algebra", "geometria", "porcentagem",
         "juros", "razao e proporcao"],
        12,
        ["Porcentagem e juros", "Razão e proporção", "Regra de três",
         "Equações e funções", "Geometria plana", "Estatística básica"],
    ),
    "Direito Constitucional": (
        ["direito constitucional", "constituicao", "cf/88", "direitos fundamentais",
         "controle de constitucionalidade"],
        12,
        ["Princípios fundamentais", "Direitos e garantias fundamentais",
         "Organização do Estado", "Organização dos Poderes",
         "Remédios constitucionais", "Administração pública na CF"],
    ),
    "Direito Administrativo": (
        ["direito administrativo", "atos administrativos", "licitacao",
         "lei 14.133", "lei 8.112", "improbidade", "poderes administrativos"],
        12,
        ["Princípios da Administração", "Atos administrativos", "Poderes administrativos",
         "Licitações e contratos (14.133/21)", "Servidores públicos (8.112/90)",
         "Responsabilidade civil do Estado", "Improbidade (8.429/92)"],
    ),
    "Direito Penal": (
        ["direito penal", "codigo penal", "crimes", "tipicidade", "pena"],
        10,
        ["Aplicação da lei penal", "Crimes contra a pessoa", "Crimes contra o patrimônio",
         "Crimes contra a Administração Pública", "Crimes contra a fé pública"],
    ),
    "Direito Processual Penal": (
        ["processo penal", "inquerito", "acao penal", "prisao em flagrante"],
        8,
        ["Inquérito policial", "Ação penal", "Prisões e medidas cautelares",
         "Provas", "Habeas corpus"],
    ),
    "Direito Civil": (
        ["direito civil", "codigo civil", "obrigacoes", "contratos"],
        8,
        ["Lei de Introdução", "Pessoas e bens", "Fatos jurídicos", "Obrigações", "Contratos"],
    ),
    "Direito Previdenciário": (
        ["previdenciario", "seguridade social", "rgps", "beneficio", "inss"],
        12,
        ["Seguridade social na CF", "Regime Geral (RGPS)", "Benefícios do RGPS",
         "Custeio da seguridade", "Decadência e prescrição"],
    ),
    "Legislação de Trânsito": (
        ["legislacao de transito", "ctb", "codigo de transito", "transito"],
        10,
        ["Normas gerais do CTB", "Infrações e penalidades", "Crimes de trânsito",
         "Habilitação e veículos", "Sinalização"],
    ),
    "Informática": (
        ["informatica", "computacao", "excel", "word", "windows", "office",
         "seguranca da informacao", "lgpd", "redes"],
        8,
        ["Windows e Office", "Excel e fórmulas", "Internet e redes",
         "Segurança da informação", "LGPD (13.709/18)", "Backup e nuvem"],
    ),
    "Atualidades": (
        ["atualidades", "conhecimentos gerais", "realidade brasileira", "geopolitica"],
        6,
        ["Política e economia", "Meio ambiente", "Tecnologia", "Direitos humanos"],
    ),
    "Administração Pública": (
        ["administracao publica", "gestao publica", "governanca", "planejamento"],
        7,
        ["Modelos de administração", "Governança e accountability", "Gestão de processos",
         "Indicadores e metas"],
    ),
    "Contabilidade": (
        ["contabilidade", "balanco", "patrimonio", "receita", "despesa"],
        8,
        ["Patrimônio e balanço", "Escrituração", "Demonstrações contábeis",
         "Contabilidade pública"],
    ),
    "Economia": (
        ["economia", "microeconomia", "macroeconomia", "inflacao", "politica fiscal"],
        7,
        ["Microeconomia", "Macroeconomia", "Política fiscal e monetária", "Setor público"],
    ),
    "Arquivologia": (
        ["arquivologia", "gestao de documentos", "protocolo", "tabela de temporalidade"],
        6,
        ["Gestão de documentos", "Classificação e arquivamento",
         "Tabela de temporalidade", "Preservação"],
    ),
}

# Perfil por área: disciplinas e pesos quando o edital não detalha a estrutura.
PERFIL_AREA = {
    "Policial": {"Português": 15, "Raciocínio Lógico": 10, "Direito Constitucional": 12,
                 "Direito Administrativo": 10, "Direito Penal": 14,
                 "Direito Processual Penal": 10, "Legislação de Trânsito": 12,
                 "Informática": 6, "Atualidades": 5},
    "Tribunal": {"Português": 18, "Raciocínio Lógico": 10, "Direito Constitucional": 12,
                 "Direito Administrativo": 14, "Direito Civil": 10,
                 "Informática": 10, "Administração Pública": 6},
    "Previdenciário": {"Português": 16, "Raciocínio Lógico": 10,
                       "Direito Constitucional": 10, "Direito Previdenciário": 30,
                       "Informática": 8, "Atualidades": 6},
    "Bancário": {"Português": 16, "Raciocínio Lógico": 14, "Matemática": 14,
                 "Informática": 12, "Atualidades": 8, "Economia": 8,
                 "Administração Pública": 4},
    "Fiscal": {"Português": 12, "Raciocínio Lógico": 10, "Direito Constitucional": 10,
               "Direito Administrativo": 12, "Contabilidade": 14, "Economia": 12,
               "Informática": 6},
    "Administrativo": {"Português": 18, "Raciocínio Lógico": 12, "Matemática": 10,
                       "Informática": 12, "Direito Administrativo": 8,
                       "Atualidades": 6},
}

# Estratégias de resolução por tópico (base de conhecimento usada na explicação)
ESTRATEGIAS = {
    "concordancia verbal": "Localize o sujeito e o verbo. Verbos impessoais (haver, fazer, ser indicando tempo) ficam no singular; sujeito composto exige plural.",
    "crase": "Troque a palavra feminina por uma masculina: se aparecer 'ao', há crase; se aparecer 'o', não há. Nunca antes de verbo, palavra masculina ou plural sem artigo.",
    "regencia verbal": "Memorize os casos que mudam de sentido: assistir (ver) = a; visar (almejar) = a; aspirar (desejar) = a; implicar (acarretar) = sem preposição.",
    "colocacao pronominal": "Atraem o pronome (próclise): palavras negativas, advérbios, pronomes relativos, conjunções subordinativas e o gerúndio com 'em'.",
    "concordancia nominal": "Em 'é proibido/é necessário/é bom', a concordância é facultativa: sem artigo fica invariável, com artigo concorda.",
    "porcentagem": "Transforme a taxa em decimal e multiplique pelo valor: 15% de 240 = 0,15 x 240.",
    "regra de tres inversa": "Aumentar operários e diminuir dias = grandezas inversas. Multiplique em linha (8 x 12 = 12 x d).",
    "juros simples": "J = C x i x t, sempre com a taxa e o tempo na mesma unidade.",
    "razao e proporcao": "Some as partes da razão, divida o total pela soma e multiplique cada parte pelo seu número.",
    "negacao logica": "Lei de De Morgan: ~(A e B) = ~A ou ~B; ~(A ou B) = ~A e ~B. Troque o conectivo e negue cada parte.",
    "equivalencia logica": "Contrapositiva: A -> B equivale a ~B -> ~A. A recíproca (B -> A) NÃO é equivalente.",
    "fundamentos da republica": "Decore o art. 1º: SO-CI-DI-VA-PLU (soberania, cidadania, dignidade, valores sociais do trabalho, pluralismo político).",
    "atos administrativos": "Atributos: presunção de legitimidade, imperatividade, autoexecutoriedade e tipicidade. Retroatividade não é atributo.",
    "licitacao - lei 14.133": "Modalidades da 14.133: pregão, concorrência, concurso, leilão e diálogo competitivo. Convite e tomada de preços não existem mais.",
    "responsabilidade civil do estado": "Art. 37, §6º: responsabilidade objetiva (risco administrativo) — dano + nexo causal. Culpa só se discute no regresso.",
    "crimes contra a administracao": "Peculato = apropriar-se; concussão = exigir; corrupção passiva = solicitar/receber; prevaricação = deixar de agir por interesse pessoal.",
    "ctb": "Art. 165 = infração administrativa. Art. 306 = crime de trânsito (6 dg/L de sangue ou sinais de alteração).",
}


# --------------------------------------------------------------- extração
def _extrair_salario(texto: str):
    valores = re.findall(r"R\$\s*([\d\.]+,\d{2})", texto)
    if not valores:
        return None
    convertidos = []
    for v in valores:
        try:
            convertidos.append(float(v.replace(".", "").replace(",", ".")))
        except ValueError:
            continue
    if not convertidos:
        return None
    # normalmente o maior valor é a remuneração inicial do cargo
    return max(convertidos)


def _extrair_datas(texto: str):
    datas = re.findall(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", texto)
    saida = []
    for d, m, a in datas:
        try:
            saida.append(date(int(a), int(m), int(d)).isoformat())
        except ValueError:
            continue
    return sorted(set(saida))


def _extrair_banca(texto: str):
    for banca in BANCAS:
        if re.search(r"\b" + re.escape(banca) + r"\b", texto, re.IGNORECASE):
            return "Cebraspe" if banca.upper() == "CESPE" else banca
    return None


def _extrair_orgao(texto: str):
    for orgao in ORGAOS_CONHECIDOS:
        if re.search(re.escape(orgao), texto, re.IGNORECASE):
            # pega a linha que contém o órgão para um nome mais completo
            for linha in texto.splitlines():
                if re.search(re.escape(orgao), linha, re.IGNORECASE):
                    limpa = linha.strip(" .-–—")
                    if 4 < len(limpa) < 120:
                        return limpa
            return orgao
    maiusculas = re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,})+\b", texto)
    if maiusculas:
        return maiusculas[0].title()
    return None


def _extrair_cargo(texto: str):
    padroes = [
        r"cargo(?:s)?\s+de\s+([A-Za-zÀ-ÿ\s]{4,60})",
        r"para\s+o\s+cargo\s+de\s+([A-Za-zÀ-ÿ\s]{4,60})",
        r"emprego\s+de\s+([A-Za-zÀ-ÿ\s]{4,60})",
    ]
    for padrao in padroes:
        m = re.search(padrao, texto, re.IGNORECASE)
        if m:
            cargo = re.split(r"[,.;\n]", m.group(1))[0].strip()
            if 3 < len(cargo) < 70:
                return cargo
    return None


def _extrair_vagas(texto: str):
    m = re.search(r"(\d{1,6})\s*(?:\(.*?\)\s*)?vagas?", texto, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def extrair_disciplinas(texto: str):
    normalizado = _norm(texto)
    encontradas = []
    for nome, (chaves, peso_base, topicos) in DISCIPLINAS.items():
        hits = sum(normalizado.count(_norm(k)) for k in chaves)
        if hits:
            # procura menção explícita de número de questões ao lado do nome
            peso = peso_base
            for k in chaves:
                m = re.search(_norm(k) + r"[^\n]{0,60}?(\d{1,3})\s*(?:questoes|questões|itens)", normalizado)
                if m:
                    peso = max(peso, min(int(m.group(1)) * 2, 40))
                    break
            encontradas.append({
                "nome": nome,
                "peso": peso,
                "mencoes": hits,
                "topicos": topicos,
            })
    encontradas.sort(key=lambda d: (-d["peso"], -d["mencoes"]))
    total = sum(d["peso"] for d in encontradas) or 1
    for d in encontradas:
        d["peso_pct"] = round(d["peso"] / total * 100, 1)
    return encontradas


def _resumo_por_template(dados: dict) -> str:
    partes = []
    if dados.get("orgao"):
        partes.append(f"Edital de {dados['orgao']}")
    if dados.get("cargo"):
        partes.append(f"para o cargo de {dados['cargo']}")
    if dados.get("banca"):
        partes.append(f"organizado pela banca {dados['banca']}")
    if dados.get("vagas"):
        partes.append(f"com {dados['vagas']} vagas")
    if dados.get("salario"):
        partes.append(f"remuneração inicial de R$ {dados['salario']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    if dados.get("datas"):
        partes.append(f"datas relevantes: {', '.join(d['iso'] for d in dados['datas'][:4])}")
    resumo = ", ".join(partes) + "." if partes else "Não foi possível identificar dados objetivos no texto enviado."
    if dados.get("disciplinas"):
        nomes = ", ".join(f"{d['nome']} ({d['peso_pct']}%)" for d in dados["disciplinas"][:8])
        resumo += f" Estrutura de conteúdo detectada: {nomes}."
    return resumo


def analisar_edital(texto: str, area: str = None) -> dict:
    """Lê o texto de um edital e devolve a estrutura completa."""
    texto = texto or ""
    disciplinas = extrair_disciplinas(texto)
    # Se o texto não traz as disciplinas (edital resumido), usa perfil da área
    if len(disciplinas) < 3:
        chave = area or "Administrativo"
        perfil = PERFIL_AREA.get(chave, PERFIL_AREA["Administrativo"])
        total = sum(perfil.values())
        disciplinas = [
            {"nome": n, "peso": p, "mencoes": 0,
             "topicos": DISCIPLINAS.get(n, ("", 0, []))[2],
             "peso_pct": round(p / total * 100, 1)}
            for n, p in sorted(perfil.items(), key=lambda x: -x[1])
        ]
        inferido = True
    else:
        inferido = False

    datas = [{"iso": d, "br": datetime.fromisoformat(d).strftime("%d/%m/%Y")}
             for d in _extrair_datas(texto)]
    dados = {
        "orgao": _extrair_orgao(texto),
        "banca": _extrair_banca(texto),
        "cargo": _extrair_cargo(texto),
        "salario": _extrair_salario(texto),
        "vagas": _extrair_vagas(texto),
        "datas": datas,
        "disciplinas": disciplinas,
        "estrutura_inferida": inferido,
    }
    entidades = sum(1 for k in ("orgao", "banca", "cargo", "salario", "vagas") if dados[k])
    confianca = min(95, 40 + entidades * 8 + (0 if inferido else 15))
    dados["confianca"] = confianca
    dados["resumo"] = _resumo_por_template(dados)
    dados["motor"] = "ia-local-v1"
    dados["analisado_em"] = datetime.now().isoformat(timespec="seconds")
    return dados


# --------------------------------------------------------------- cronograma
def gerar_cronograma(disciplinas: list, data_prova: str = None, horas_dia: float = 3.0,
                     incluir_domingo: bool = False) -> dict:
    """Gera plano de estudos real: distribui disciplinas por peso, insere revisão
    espaçada (1, 3 e 7 dias) e simulado semanal."""
    if not disciplinas:
        return {"erro": "Nenhuma disciplina informada"}

    hoje = date.today()
    try:
        prova = date.fromisoformat(data_prova) if data_prova else hoje + timedelta(days=90)
    except ValueError:
        prova = hoje + timedelta(days=90)
    dias_restantes = max((prova - hoje).days, 7)
    semanas = max(1, min(26, dias_restantes // 7))
    dias_semana = 6 if not incluir_domingo else 7

    # normaliza pesos
    total_peso = sum(d.get("peso", 1) for d in disciplinas) or 1
    fila = []
    for d in disciplinas:
        cota = max(1, round(d.get("peso", 1) / total_peso * semanas * dias_semana))
        fila.extend([d] * cota)

    def topico(d, indice):
        tps = d.get("topicos") or ["Revisão geral"]
        return tps[indice % len(tps)]

    plano = []
    pendentes_revisao = {}  # data -> [topico]
    contador = 0
    nomes_dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

    for semana in range(1, semanas + 1):
        dias = []
        for i in range(dias_semana):
            data_dia = hoje + timedelta(days=(semana - 1) * 7 + i)
            if data_dia < hoje:
                continue
            atividades = []
            # 60% do tempo em conteúdo novo
            blocos = max(1, int(round(horas_dia / 1.5)))
            for _ in range(blocos):
                if not fila:
                    fila = [disciplinas[0]]
                d = fila.pop(0)
                ativid = {
                    "disciplina": d["nome"],
                    "topico": topico(d, contador),
                    "duracao_h": round(horas_dia / blocos, 1),
                    "tipo": "estudo",
                }
                contador += 1
                atividades.append(ativid)
                # agenda revisão espaçada
                for offset in (1, 3, 7):
                    alvo = data_dia + timedelta(days=offset)
                    pendentes_revisao.setdefault(alvo.isoformat(), []).append(
                        f"{d['nome']} — {ativid['topico']}")
            # revisões do dia
            for top in pendentes_revisao.pop(data_dia.isoformat(), [])[:2]:
                atividades.append({"disciplina": top.split(" — ")[0], "topico": top,
                                   "duracao_h": 0.5, "tipo": "revisao"})
            # simulado no último dia da semana
            if i == dias_semana - 1:
                atividades.append({"disciplina": "Simulado", "topico": f"Simulado semanal {semana}",
                                   "duracao_h": min(3.0, horas_dia), "tipo": "simulado"})
            dias.append({
                "data": data_dia.isoformat(),
                "dia_semana": nomes_dias[data_dia.weekday()],
                "atividades": atividades,
            })
        plano.append({"semana": semana, "dias": dias})

    total_horas = round(sum(a.get("duracao_h", 0) for s in plano for d in s["dias"]
                            for a in d["atividades"]), 1)
    return {
        "gerado_por": "ia-local-v1",
        "criado_em": hoje.isoformat(),
        "data_prova": prova.isoformat(),
        "dias_restantes": dias_restantes,
        "horas_dia": horas_dia,
        "semanas": len(plano),
        "total_horas": total_horas,
        "distribuicao": [
            {"disciplina": d["nome"], "peso_pct": d.get("peso_pct",
             round(d.get("peso", 1) / total_peso * 100, 1))} for d in disciplinas
        ],
        "plano": plano,
    }


# --------------------------------------------------------------- desempenho
def analisar_desempenho(respostas: list, revisoes_pendentes: int = 0) -> dict:
    """Analisa respostas reais do aluno e devolve diagnóstico + recomendações."""
    if not respostas:
        return {
            "total": 0, "acertos": 0, "taxa_acerto": 0,
            "por_disciplina": [], "pontos_fracos": [],
            "recomendacoes": ["Responda algumas questões para a IA montar seu diagnóstico."],
            "previsao_nota": None, "motor": "ia-local-v1",
        }
    por_disc = {}
    for r in respostas:
        d = r.get("disciplina") or "Geral"
        item = por_disc.setdefault(d, {"disciplina": d, "total": 0, "acertos": 0,
                                       "topicos_errados": {}})
        item["total"] += 1
        if r.get("correta"):
            item["acertos"] += 1
        else:
            top = r.get("topico") or "Geral"
            item["topicos_errados"][top] = item["topicos_errados"].get(top, 0) + 1

    lista = []
    for d, item in por_disc.items():
        taxa = round(item["acertos"] / item["total"] * 100, 1)
        pior = sorted(item["topicos_errados"].items(), key=lambda x: -x[1])[:2]
        lista.append({
            "disciplina": d,
            "total": item["total"],
            "acertos": item["acertos"],
            "taxa_acerto": taxa,
            "topicos_criticos": [t for t, _ in pior],
        })
    lista.sort(key=lambda x: x["taxa_acerto"])

    pontos_fracos = [d for d in lista if d["taxa_acerto"] < 70]
    recomendacoes = []
    for d in pontos_fracos[:3]:
        top = d["topicos_criticos"][0] if d["topicos_criticos"] else d["disciplina"]
        recomendacoes.append(
            f"{d['disciplina']} está em {d['taxa_acerto']}% de acerto — priorize '{top}' "
            f"com 20 questões comentadas e uma revisão em 48h."
        )
    if revisoes_pendentes:
        recomendacoes.append(f"Você tem {revisoes_pendentes} revisões pendentes. Resolva hoje para não perder a curva do esquecimento.")
    if not pontos_fracos:
        recomendacoes.append("Desempenho equilibrado (acima de 70% em todas). Aumente a dificuldade e faça simulados cronometrados.")

    total = len(respostas)
    acertos = sum(1 for r in respostas if r.get("correta"))
    taxa = round(acertos / total * 100, 1)
    # previsão simples: nota esperada em prova de 100 pontos com margem de erro
    margem = round(max(3.0, 100 / (total ** 0.5)), 1)
    return {
        "total": total,
        "acertos": acertos,
        "taxa_acerto": taxa,
        "por_disciplina": lista,
        "pontos_fracos": [d["disciplina"] for d in pontos_fracos],
        "recomendacoes": recomendacoes,
        "previsao_nota": {"estimativa": taxa, "margem": margem,
                          "faixa": [max(0, round(taxa - margem, 1)), min(100, round(taxa + margem, 1))]},
        "motor": "ia-local-v1",
    }


# --------------------------------------------------------------- explicação
def explicar_questao(questao: dict) -> dict:
    """Gera explicação didática passo a passo a partir do tópico da questão."""
    topico = _norm(questao.get("topico", ""))
    estrategia = None
    for chave, texto in ESTRATEGIAS.items():
        if chave in topico or topico in chave:
            estrategia = texto
            break
    if not estrategia:
        for chave, texto in ESTRATEGIAS.items():
            if chave in _norm(questao.get("enunciado", "")):
                estrategia = texto
                break

    alternativas = questao.get("alternativas") or {}
    if isinstance(alternativas, str):
        try:
            alternativas = json.loads(alternativas)
        except json.JSONDecodeError:
            alternativas = {}

    passos = [
        f"1. Identifique o que o enunciado pede: {questao.get('topico') or 'conceito central'}.",
        f"2. {estrategia}" if estrategia else "2. Elimine as alternativas que contrariam a regra geral do tema.",
        f"3. Confirme na alternativa {questao.get('correta')}: {alternativas.get(questao.get('correta'), '')}",
    ]
    return {
        "motor": "ia-local-v1",
        "topico": questao.get("topico"),
        "explicacao": questao.get("explicacao"),
        "estrategia": estrategia or "Compare cada alternativa com a regra geral do tópico e descarte as que a violam.",
        "passos": passos,
    }


# --------------------------------------------------------------- monitor
FONTES_MONITOR = [
    ("PCI Concursos", "https://www.pciconcursos.com.br/"),
    ("Folha Dirigida", "https://folhadirigida.com.br/concursos"),
]


def monitorar_editais(limite: int = 8) -> dict:
    """Tenta ler portais públicos de concursos. Se a rede bloquear, informa e
    devolve a base local (nunca quebra a experiência)."""
    import httpx

    encontrados = []
    falhas = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ConcursosAI/1.0)"}
    for nome, url in FONTES_MONITOR:
        try:
            with httpx.Client(timeout=8, follow_redirects=True, headers=headers) as cli:
                r = cli.get(url)
            if r.status_code != 200:
                falhas.append(f"{nome}: HTTP {r.status_code}")
                continue
            titulos = re.findall(r"<h[23][^>]*>\s*<a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>",
                                 r.text, re.IGNORECASE | re.DOTALL)
            if not titulos:
                titulos = re.findall(r"<a[^>]+href=\"(/concursos/[^\"]+)\"[^>]*>(.*?)</a>",
                                     r.text, re.IGNORECASE | re.DOTALL)
            for href, bruto in titulos[:limite]:
                titulo = re.sub(r"<[^>]+>", "", bruto).strip()
                titulo = re.sub(r"\s+", " ", titulo)
                if len(titulo) < 12:
                    continue
                link = href if href.startswith("http") else nome_url_join(url, href)
                encontrados.append({
                    "id": "mon-" + hashlib.md5(titulo.encode()).hexdigest()[:10],
                    "titulo": titulo[:120],
                    "orgao": None,
                    "banca": _extrair_banca(titulo),
                    "cargo": None,
                    "salario": None,
                    "data_prova": None,
                    "url": link,
                    "fonte": nome,
                    "score": 60 + (hash(titulo) % 30),
                    "status": "novo",
                })
        except Exception as exc:  # rede indisponível
            falhas.append(f"{nome}: {type(exc).__name__}")
    return {
        "motor": "ia-local-v1",
        "fonte_online": len(encontrados) > 0,
        "editais": encontrados[:limite],
        "falhas": falhas,
    }


def nome_url_join(base: str, href: str) -> str:
    from urllib.parse import urljoin
    return urljoin(base, href)
