# 🧠 Agente de Tradução NL ↔ CPC

**Projeto para a disciplina de Lógica para Computação – Engenharia de Software**

Este repositório contém um agente inteligente capaz de traduzir frases da Linguagem Natural (português) para Cálculo Proposicional Clássico (CPC) e também realizar o caminho inverso. O sistema foi desenvolvido em Python (Flask) com técnicas de Processamento de Linguagem Natural (spaCy) e análise simbólica via SymPy, acompanhado por uma interface Web desenvolvida em HTML/JS.

---

## 📋 Índice

- [Instalação e Configuração](#instalação-e-configuração)
- [Como Usar](#como-usar)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Estratégias de Tradução](#estratégias-de-tradução)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Exemplos de Uso](#exemplos-de-uso)
- [Limitações Conhecidas](#limitações-conhecidas)

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone ou baixe este repositório**

2. **Instale as dependências do projeto:**
   ```bash
   pip install -r requerimentos.txt
   ```

3. **Baixe o modelo de português do spaCy:**
   ```bash
   python -m spacy download pt_core_news_sm
   ```
   ⚠️ **Importante:** Este passo é obrigatório! O sistema precisa do modelo de português para funcionar corretamente.

4. **Execute o servidor Flask:**
   ```bash
   python app.py
   ```
   O servidor estará rodando em `http://127.0.0.1:5000`

5. **Abra a interface web:**
   - Abra o arquivo `index.html` no seu navegador
   - Ou acesse diretamente via caminho do arquivo
   - A interface se conectará automaticamente com a API em `http://127.0.0.1:5000`

---

## 💡 Como Usar

A interface web possui duas abas principais para realizar as traduções:

### Tradução NL → CPC (Linguagem Natural para Cálculo Proposicional)

1. Selecione a aba **"Linguagem Natural → CPC"**
2. Digite uma frase em português no campo de texto
3. Clique em **"Traduzir para CPC"**
4. O sistema retornará:
   - A fórmula em CPC
   - O mapeamento das proposições atômicas (P, Q, R, etc.)

**Exemplo:**
- **Entrada:** "Se chover e fizer frio, fique em casa."
- **Saída:**
  - Fórmula: `(P ∧ Q) → R`
  - Mapeamento: `P = chover`, `Q = fizer frio`, `R = fique em casa`

### Tradução CPC → NL (Cálculo Proposicional para Linguagem Natural)

1. Selecione a aba **"CPC → Linguagem Natural"**
2. Digite a fórmula em CPC no campo "Fórmula em CPC"
   - Aceita formatos como: `p^¬q`, `p∧q`, `p v q`, `p∨q`, `p->q`, `p→q`, `p<->q`, `p↔q`
3. Digite o mapeamento em formato JSON no campo "Mapeamento"
   - Exemplo: `{"p": "Serena é uma gata", "q": "Serena come peixe"}`
4. Clique em **"Traduzir para Português"**
5. O sistema retornará a frase em português correspondente

**Exemplo:**
- **Fórmula:** `p^¬q`
- **Mapeamento:** `{"p": "Serena é uma gata", "q": "Serena come peixe"}`
- **Saída:** "Serena é uma gata e não Serena come peixe."

---

## 🏗️ Arquitetura do Sistema

O sistema é composto por duas camadas principais que se comunicam via requisições HTTP usando JSON:

```
┌───────────────────────────┐
│         Usuário           │
│  (navegador / interface)  │
└───────────────┬───────────┘
                │  envia JSON
                ▼
┌──────────────────────────────────┐
│           Front-end             │
│   (index.html + JavaScript)     │
│ - Envia frase NL → API          │
│ - Envia fórmula CPC → API       │
│ - Exibe resposta ao usuário     │
└──────────────────┬──────────────┘
                   │ requisição POST
                   ▼
┌──────────────────────────────────┐
│              API Flask           │
│             (app.py)             │
│                                  │
│ Endpoints:                       │
│  • /api/nl-to-cpc                │
│      - Recebe frase              │
│      - Limpa e normaliza texto   │
│      - Identifica conectivos     │
│      - Gera fórmula em CPC       │
│                                  │
│  • /api/cpc-to-nl                │
│      - Recebe fórmula            │
│      - Transforma em SymPy       │
│      - Reconstrói frase NL       │
└──────────────────┬──────────────┘
                   │
                   ▼
         Resposta JSON retorna
```

### Fluxo de Dados

1. **Frontend (index.html):** Interface visual onde o usuário interage
2. **Backend (app.py):** API Flask que processa as requisições
3. **spaCy:** Tokeniza e normaliza a frase em português
4. **Regras linguísticas:** Detectam conectivos como "e", "ou", "mas", "se... então..."
5. **Módulo de extração:** Mapeia conteúdos para proposições atômicas (P, Q, R...)
6. **SymPy:** Interpreta fórmulas proposicionais e reconstrói frases
7. **Resposta JSON:** Retorna o resultado formatado para o frontend

---

## 🔄 Estratégias de Tradução

### Tradução de Linguagem Natural → CPC

O sistema usa uma abordagem híbrida combinando:

#### 1. Regras Linguísticas Heurísticas

Baseadas na estrutura do português, o sistema reconhece os seguintes conectivos:

| Linguagem Natural | CPC |
|-------------------|-----|
| "e" / "mas" | ∧ |
| "ou" | ∨ |
| "não X" | ¬X |
| "se X então Y" | X → Y |
| "X se e somente se Y" | X ↔ Y |

#### 2. Normalização com spaCy

- **Tokenização:** Divide o texto em unidades menores
- **Remoção de ruído:** Limpa espaços extras e caracteres desnecessários
- **Padronização:** Normaliza variações de "não" (nao, nâo, năo, ñao → "não")

#### 3. Extração de Proposições Atômicas

O sistema divide a frase em partes menores e mapeia cada proposição para uma letra:

**Exemplo:**
- Frase: "chover e fizer frio"
- Proposições: `P = chover`, `Q = fizer frio`

#### 4. Construção da Fórmula Final

A função `construir_formula_cpc()` monta a estrutura recursivamente:
- Identifica o conectivo principal
- Resolve negações
- Mapeia recursivamente as partes da frase

### Tradução de CPC → Linguagem Natural

Esta parte usa o SymPy para converter a fórmula em um objeto lógico:

**Exemplos interpretados pelo SymPy:**
- `~P` → `Not(P)`
- `P & Q` → `And(P, Q)`
- `P | Q` → `Or(P, Q)`
- `P >> Q` → `Implies(P, Q)`
- `P >>= Q` → `Equivalent(P, Q)`

**Reconstrução literal:**
- `Not(X)` → "não X"
- `And(X, Y)` → "X e Y"
- `Or(X, Y)` → "X ou Y"
- `Implies(X, Y)` → "Se X, então Y"
- `Equivalent(X, Y)` → "X se e somente se Y"

---

## 🛠️ Tecnologias Utilizadas

- **Flask:** Framework web Python para criar a API REST
- **Flask-CORS:** Habilita requisições cross-origin entre frontend e backend
- **spaCy:** Biblioteca de Processamento de Linguagem Natural para português
- **SymPy:** Biblioteca Python para manipulação simbólica de fórmulas lógicas
- **HTML/CSS/JavaScript:** Tecnologias web para a interface do usuário
- **Bootstrap 5:** Framework CSS para estilização responsiva

---

## 📁 Estrutura do Projeto

```
trabalho_marcio/
│
├── app.py                 # Backend Flask com endpoints da API
├── index.html             # Interface web (frontend)
├── requerimentos.txt      # Dependências do projeto
├── observacoes.txt        # Documentação técnica detalhada
└── README.md              # Este arquivo
```

### Descrição dos Arquivos

- **app.py:** Contém toda a lógica do backend:
  - Funções de normalização de texto
  - Detecção de conectivos linguísticos
  - Extração e mapeamento de proposições atômicas
  - Construção de fórmulas CPC
  - Conversão entre CPC e SymPy
  - Endpoints da API (`/api/nl-to-cpc` e `/api/cpc-to-nl`)

- **index.html:** Interface web completa:
  - Duas abas para diferentes tipos de tradução
  - Formulários para entrada de dados
  - Exibição de resultados formatados
  - Comunicação com API via JavaScript (fetch)

- **requerimentos.txt:** Lista de dependências Python necessárias

- **observacoes.txt:** Documentação técnica detalhada do projeto, incluindo decisões de design e exemplos

---

## 📚 Exemplos de Uso

### Exemplo 1: NL → CPC (com implicação e conjunção)

**Entrada:**
```
Se chover e fizer frio, fique em casa.
```

**Saída:**
```
Fórmula em CPC: (P ∧ Q) → R

Mapeamento:
{
  "P": "chover",
  "Q": "fizer frio",
  "R": "fique em casa"
}
```

**Análise:** A API reconhece "se..., então..." como `→`. Dentro do antecedente, "e" vira `∧`.

---

### Exemplo 2: NL → CPC (com negação)

**Entrada:**
```
Kiki não é uma gata, mas Kiki come de tudo.
```

**Saída:**
```
Fórmula em CPC: (¬P ∧ Q)

Mapeamento:
{
  "P": "kiki é uma gata",
  "Q": "kiki come de tudo"
}
```

**Análise:** O sistema identifica "mas" como conjunção (`∧`) e trata "não é uma gata" como negação (`¬P`).

---

### Exemplo 3: CPC → NL

**Entrada JSON:**
```json
{
  "formula": "p^¬q",
  "mapeamento": {
    "p": "Serena é uma gata",
    "q": "Serena come peixe"
  }
}
```

**Saída:**
```
Frase em Linguagem Natural: Serena é uma gata e não Serena come peixe.
```

---

### Exemplo 4: CPC → NL (com implicação)

**Entrada JSON:**
```json
{
  "formula": "(p v q)->r",
  "mapeamento": {
    "p": "chover",
    "q": "nevar",
    "r": "ficar em casa"
  }
}
```

**Saída:**
```
Frase em Linguagem Natural: Se chover ou nevar, então ficar em casa.
```

---

## ⚠️ Limitações Conhecidas

### Limitações Atuais

1. **Português ambíguo:** Frases complexas dificultam a identificação automática de proposições. O sistema opera principalmente por regras heurísticas, não por compreensão semântica profunda.

2. **Reconstrução literal:** A saída CPC → NL não ajusta a gramática perfeitamente. Por exemplo, pode gerar "não Serena come peixe" em vez de "Serena não come peixe".

3. **Sem compreensão semântica real:** O sistema opera apenas por regras, não por interpretação profunda do significado das frases.

4. **Frases complexas:** Não suporta adequadamente frases com múltiplos níveis sintáticos complexos, como:
   - "Se chover ou nevar e eu estiver cansada, então talvez eu fique em casa."

5. **spaCy limitado:** O spaCy ainda não faz parsing completo para lógica proposicional, então o entendimento depende das heurísticas implementadas.

### Possíveis Melhorias Futuras

- Implementar parser sintático real com árvores de dependência
- Criar módulo de geração de linguagem natural suave (NLG) para melhorar a saída
- Adicionar interface com LLMs para melhorar desambiguação
- Implementar suporte para:
  - Parênteses explícitos em linguagem natural
  - Dupla negação
  - Conectivos múltiplos na mesma frase de forma mais robusta
- Hospedar a API online (Render / Vercel) para demonstração

---

## 👥 Autores

- **Felipe Dos Santos Silva** - 25964
- **Thales Fratarcangeli de Carvalho** - 26342
- **Maria Gabriela Orlandini** - 25963

---

## 📝 Notas Finais

Este trabalho demonstra, na prática, como podemos unir sistemas simbólicos e processamento textual moderno para criar agentes inteligentes interpretáveis. A arquitetura construída aplica conceitos fundamentais de Lógica Proposicional, PLN e desenvolvimento Web.

---

**Desenvolvido para a disciplina de Lógica para Computação – Engenharia de Software**

