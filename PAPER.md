# Agent Skills Orientadas a Objetos: Arquitetura Modular para Agentes de IA Escaláveis

**Autor:** Gustavo Stork
**Data:** Março de 2026
**Versão:** 5.0

---

## Resumo

Os agentes de IA atuais sofrem de um problema estrutural: prompts monolíticos que consomem contexto desnecessariamente e resistem à manutenção. Com a abertura do padrão Agent Skills pela Anthropic (18/Dez/2025) e a subsequente publicação do guia oficial *"The Complete Guide to Building Skills for Claude"* (Fev/2026), a comunidade ganhou fundamentos sólidos para criar skills individuais de qualidade.

Porém, o guia oficial trata skills como unidades independentes e não aborda o que acontece quando múltiplas skills precisam operar em conjunto. Este paper propõe a camada arquitetural complementar: tratar Skills como objetos comportamentais — unidades encapsuladas que podem ser compostas hierarquicamente, seguindo princípios SOLID. Demonstramos a viabilidade através de **três implementações em domínios distintos** — otimização de conteúdo (SEO/GEO), code review (desenvolvimento de software) e análise de investimentos (finanças) — e validamos a necessidade através de um **case study real** (Seção 8) onde um sistema de 7 skills bem construídas sofreu degradação silenciosa sob composição não-gerenciada. Apresentamos estratégias concretas para mitigar custos de contexto e propomos mecanismos de resolução de dependências compatíveis com o padrão atual.

**Palavras-chave:** Agent Skills, OOP, SOLID, Prompt Engineering, AI Agents, Composição, Modularidade, Context Budget

---

## 1. Introdução

### 1.1 O Problema

System prompts tradicionais operam como variáveis globais: sempre presentes, sempre consumindo tokens, impossíveis de modularizar. À medida que agentes ganham capacidades, esses prompts crescem até se tornarem ingerenciáveis.

Agent Skills resolvem parte do problema através de progressive disclosure — carregamento sob demanda. Porém, o padrão atual é plano: Skills são independentes, sem mecanismos nativos para expressar dependências ou hierarquias.

### 1.2 A Proposta

Argumentamos que Skills podem — e devem — ser tratadas como classes em Programação Orientada a Objetos:

- **Encapsulamento:** Cada Skill isola seu conhecimento e comportamento.
- **Composição:** Skills complexas delegam para Skills especializadas.
- **Abstração:** Skills "base" definem contratos que derivadas implementam.
- **Reutilização:** Conhecimento compartilhado vive em um único lugar (DRY).

> **Nota sobre terminologia:** Usamos "herança" metaforicamente. Tecnicamente, o mecanismo é composição — uma Skill carrega outra em seu contexto. Argumentamos que isso é preferível à herança verdadeira, alinhando-se ao princípio "favor composition over inheritance" do GoF.

### 1.3 Relação com o Guia Oficial da Anthropic

Em fevereiro de 2026, a Anthropic publicou *"The Complete Guide to Building Skills for Claude"* — o primeiro guia oficial e abrangente sobre design de Agent Skills. O documento estabelece fundamentos importantes: estrutura de diretórios (SKILL.md + frontmatter YAML), o princípio de Progressive Disclosure em três níveis (frontmatter → body → linked files), categorias de uso (Document Creation, Workflow Automation, MCP Enhancement), e boas práticas para triggers, instruções e exemplos.

Este paper reconhece e se alinha ao guia oficial. Porém, há uma lacuna deliberada no escopo da Anthropic: **o guia trata cada skill como uma unidade independente**. Ele menciona composability — "your skill should work well alongside others" — mas não oferece mecanismos para gerenciar composição, expressar dependências entre skills, ou garantir qualidade quando múltiplas skills operam simultaneamente.

A lacuna não é acidental. O guia da Anthropic é um *Getting Started* — pragmático, focado em criar skills individuais que funcionem bem. Este paper ocupa o espaço seguinte: **a camada arquitetural para sistemas de skills em produção**. A relação entre os dois é complementar:

| Aspecto | Guia Oficial da Anthropic | Este Paper |
|---------|---------------------------|------------|
| Escopo | Skill individual | Sistema de skills |
| Pergunta central | "Como fazer uma skill boa?" | "Como organizar skills que escalam?" |
| Composição | Mencionada, não mecanizada | Hierarquias, contratos, dependency resolution |
| Qualidade | Boas práticas de escrita | Contract testing, validation gates |
| Contexto | Progressive Disclosure (3 níveis) | Progressive Loading ([SUMMARY]/[FULL]) + budget |
| Reprodutibilidade | Não abordada | Lockfiles, logging estruturado, snapshots |

A Seção 8 deste paper (Case Study) demonstra empiricamente por que essa camada é necessária, usando um sistema real de produção que segue o guia oficial mas sofre degradação quando múltiplas skills competem por contexto.

---

## 2. Mapeamento Conceitual: OOP → Agent Skills

| Conceito OOP | Implementação em Skills | Exemplo |
|--------------|-------------------------|---------|
| Classe Abstrata | Skill com `type: abstract` (apenas regras/definições) | `seo-knowledge-base` |
| Composição | Instrução `LOAD CONTEXT: "skill-name"` | Optimizer carrega Base |
| Interface | Schema de I/O no `metadata.json` | Contrato de input/output |
| Polimorfismo | Múltiplas Skills implementando mesmo schema | SEO-Auditor vs GEO-Auditor |
| Factory | Orquestrador que instancia Skills conforme contexto | `content-orchestrator` |
| Dependency Injection | Skills passadas como parâmetro, não hardcoded | Configurável em runtime |

### 2.1 O "Runtime" de Skills

Em linguagens compiladas, herança é resolvida em compile-time. Em Skills, a composição ocorre em **inference-time**: quando o agente decide carregar uma Skill, ela é injetada no contexto atual. Isso traz flexibilidade (composição dinâmica) mas também custos (tokens adicionais por "import").

---

## 3. Aplicando SOLID a Agent Skills

### S — Single Responsibility Principle

> Uma Skill deve ter apenas uma razão para mudar.

**Anti-pattern:** Uma Skill que "analisa SEO, reescreve conteúdo e publica no CMS".

**Pattern correto:**
- `seo-auditor` → apenas análise
- `content-writer` → apenas escrita
- `cms-publisher` → apenas publicação

### O — Open/Closed Principle

> Skills devem estar abertas para extensão, fechadas para modificação.

A `seo-knowledge-base` pode receber novas regras (extensão) sem que o `geo-optimizer` precise ser alterado (fechado). O optimizer simplesmente carrega a base atualizada.

### L — Liskov Substitution Principle

> Skills derivadas devem ser substituíveis por suas bases.

Se um fluxo espera um "otimizador de texto", tanto `seo-optimizer` quanto `geo-optimizer` devem funcionar — ambos aceitam texto e retornam texto otimizado, apenas com estratégias diferentes.

### I — Interface Segregation Principle

> Muitas interfaces específicas são melhores que uma interface geral.

Em vez de um `metadata.json` genérico que aceita "qualquer coisa", defina schemas específicos:

```json
{
  "input_schema": {
    "type": "object",
    "properties": {
      "content": { "type": "string" },
      "target_score": { "type": "number", "minimum": 0, "maximum": 100 }
    },
    "required": ["content"]
  }
}
```

### D — Dependency Inversion Principle

> Dependa de abstrações, não de implementações.

O `content-orchestrator` não deve chamar `geo-optimizer` diretamente. Deve chamar "um otimizador" — qual implementação usar pode ser configurável ou decidido em runtime baseado no contexto.

---

## 4. Arquitetura de Referência: Sistema SEO/GEO

```
┌─────────────────────────────────────────────────────────────┐
│                         User                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  content-orchestrator                       │
│                    (Orquestração)                           │
└───────┬─────────────────┬─────────────────┬─────────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  seo-auditor  │ │ geo-optimizer │ │content-writer │
│(Especialização)│ │(Especialização)│ │ (Utilitário)  │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └────────────┬────┴────────────┬────┘
                     │                 │
                     ▼                 ▼
        ┌─────────────────────────────────────┐
        │        seo-knowledge-base           │
        │           (Abstração)               │
        │  ┌─────────────────────────────┐    │
        │  │ [SUMMARY] Visão geral       │    │
        │  │ [FULL] Detalhes completos   │    │
        │  └─────────────────────────────┘    │
        └─────────────────────────────────────┘
```

### 4.1 Descrição das Camadas

| Camada | Skill | Responsabilidade |
|--------|-------|------------------|
| Abstração | `seo-knowledge-base` | Regras E-E-A-T, Core Web Vitals, diretrizes GEO. Nunca executa, apenas define. |
| Especialização | `geo-optimizer` | Transforma texto para otimização em AI Search. Carrega a base. |
| Utilitário | `seo-auditor` | Valida conformidade contra a base. Retorna score + sugestões. |
| Orquestração | `content-orchestrator` | Coordena o fluxo: gerar → auditar → otimizar → validar. |

### 4.2 Generalização: Code Review (Desenvolvimento de Software)

Para demonstrar que o padrão é generalizável, aplicamos a mesma arquitetura ao domínio de code review:

```
┌─────────────────────────────────────────┐
│       code-review-orchestrator          │
│            (Orquestração)               │
└─────────┬───────────────┬───────────────┘
          │               │
          ▼               ▼
   ┌──────────────┐ ┌──────────────────┐
   │   security-  │ │   performance-   │
   │    auditor   │ │    optimizer     │
   │(Especialização)│ │(Especialização) │
   └──────┬───────┘ └────────┬─────────┘
          │                  │
          └─────────┬────────┘
                    ▼
       ┌──────────────────────────┐
       │   code-standards-base    │
       │       (Abstração)        │
       │  ┌────────────────────┐  │
       │  │ OWASP Top 10       │  │
       │  │ SOLID Principles   │  │
       │  │ Performance Rules  │  │
       │  └────────────────────┘  │
       └──────────────────────────┘
```

| Camada | Skill | Responsabilidade |
|--------|-------|------------------|
| Abstração | `code-standards-base` | OWASP Top 10, SOLID, Clean Code, patterns de performance |
| Especialização | `security-auditor` | Detecta vulnerabilidades (SQL Injection, XSS, etc.) |
| Especialização | `performance-optimizer` | Otimiza complexidade O(n), memory, I/O |
| Orquestração | `code-review-orchestrator` | Coordena review completo com scoring unificado |

**Observação sobre o meta-exemplo:** Note a ironia produtiva — usamos OOP para ensinar agentes a fazer review de código que deve seguir princípios... OOP. A skill `code-standards-base` contém regras SOLID que ela mesma exemplifica.

### 4.3 Generalização: Análise Financeira (Finance)

Para provar aplicabilidade fora de tecnologia, aplicamos ao domínio financeiro:

```
┌─────────────────────────────────────────┐
│       investment-orchestrator           │
│            (Orquestração)               │
└─────────┬───────────────┬───────────────┘
          │               │
          ▼               ▼
   ┌──────────────┐ ┌──────────────────┐
   │    risk-     │ │    portfolio-    │
   │   analyzer   │ │    optimizer     │
   │(Especialização)│ │(Especialização) │
   └──────┬───────┘ └────────┬─────────┘
          │                  │
          └─────────┬────────┘
                    ▼
       ┌──────────────────────────┐
       │  financial-rules-base    │
       │       (Abstração)        │
       │  ┌────────────────────┐  │
       │  │ VaR, Sharpe, Beta  │  │
       │  │ Modern Portfolio   │  │
       │  │ Compliance Rules   │  │
       │  └────────────────────┘  │
       └──────────────────────────┘
```

| Camada | Skill | Responsabilidade |
|--------|-------|------------------|
| Abstração | `financial-rules-base` | VaR, Sharpe Ratio, MPT, regras de compliance |
| Especialização | `risk-analyzer` | Calcula métricas de risco do portfólio |
| Especialização | `portfolio-optimizer` | Otimiza alocação via fronteira eficiente |
| Orquestração | `investment-orchestrator` | Análise completa com plano de ação |

**Observação sobre domínio não-técnico:** Este exemplo demonstra que a arquitetura funciona para qualquer domínio com regras estruturadas — não apenas para desenvolvedores. Profissionais de finanças, compliance, ou analistas podem construir skills hierárquicas sem conhecimento de programação.

### 4.4 Padrão Comum Entre Domínios

Os três exemplos revelam um padrão arquitetural consistente:

```
[Orchestrator] ─────────────────────────────────
       │                                        │
       ├── [Specialized Skill A] ──┐            │  Domínio
       │                           ├── [Base]   │  Específico
       └── [Specialized Skill B] ──┘            │
                                   ─────────────
```

| Componente | SEO/GEO | Code Review | Finance |
|------------|---------|-------------|---------|
| Base | `seo-knowledge-base` | `code-standards-base` | `financial-rules-base` |
| Analyzer | `seo-auditor` | `security-auditor` | `risk-analyzer` |
| Optimizer | `geo-optimizer` | `performance-optimizer` | `portfolio-optimizer` |
| Orchestrator | `content-orchestrator` | `code-review-orchestrator` | `investment-orchestrator` |

**Contratos comuns (polimorfismo):**
- `analyze(input) → Report` — implementado por todos os analyzers
- `optimize(input) → OptimizedOutput` — implementado por todos os optimizers
- `orchestrate(input) → UnifiedReport` — implementado por todos os orchestrators

---

## 5. Implementação de Referência

### 5.1 Estrutura de Diretórios

```
/skills
├── seo-knowledge-base/
│   ├── SKILL.md
│   └── metadata.json
├── geo-optimizer/
│   ├── SKILL.md
│   └── metadata.json
├── seo-auditor/
│   ├── SKILL.md
│   └── metadata.json
└── content-orchestrator/
    ├── SKILL.md
    └── metadata.json
```

### 5.2 Skill Base com Progressive Loading (seo-knowledge-base/SKILL.md)

```markdown
---
name: seo-knowledge-base
version: 1.2.0
type: abstract
description: Fonte de verdade para regras de SEO e GEO. Skill abstrata — não invocar diretamente.
tags: [seo, geo, rules, abstract]
---

# SEO & GEO Knowledge Base

## GUARD
Se você foi invocado diretamente (não via outra skill que declare dependência),
responda: "Esta é uma skill abstrata. Use `geo-optimizer` ou `seo-auditor`."

## PROPÓSITO
Esta skill é uma **ABSTRAÇÃO**. Ela não executa ações — apenas fornece
definições que outras skills devem carregar e aplicar.

---

## [SUMMARY]

### Visão Geral das Regras

**E-E-A-T (Google):** Experience, Expertise, Authoritativeness, Trustworthiness.
Conteúdo deve demonstrar uso real, citar fontes verificáveis, referenciar
autoridades e manter transparência.

**GEO (Generative Engine Optimization):** Estruturar conteúdo para parsing por
IAs. Usar formato "Segundo [Autoridade], [Fato]". Preferir listas e tabelas.
Alta densidade informacional (fatos/token).

**Métodos abstratos:** `analyze(content)`, `optimize(content)`

---

## [FULL]

### Regras E-E-A-T Detalhadas

#### Experience (Experiência)
- Conteúdo deve demonstrar uso real do produto/serviço
- Incluir casos de uso específicos, não apenas teoria
- Evitar generalidades; preferir exemplos concretos

#### Expertise (Especialização)
- Citar fontes técnicas verificáveis
- Usar terminologia correta do domínio
- Demonstrar profundidade de conhecimento

#### Authoritativeness (Autoridade)
- Referenciar domínios de alta autoridade (.gov, .edu, papers)
- Evitar fontes anônimas ou não verificáveis
- Incluir credenciais quando relevante

#### Trustworthiness (Confiabilidade)
- HTTPS obrigatório para links
- Evitar táticas de clickbait
- Declarar conflitos de interesse
- Manter consistência factual

### Regras GEO Detalhadas

#### Estrutura para AI Parsing
- Usar formato: "Segundo [Autoridade], [Fato verificável]"
- Preferir listas e tabelas (facilita extração por LLMs)
- Manter alta densidade informacional (fatos/token)
- Evitar ambiguidade; ser preciso

#### Otimização de Citação
- IAs priorizam conteúdo que pode ser citado com atribuição clara
- Incluir estatísticas com fonte e data
- Formato ideal: "[Métrica] segundo [Fonte] ([Ano])"

### [ABSTRACT] Métodos a Implementar
- `analyze(content) → ComplianceReport`
- `optimize(content) → OptimizedContent`
```

### 5.3 Skill Especializada (geo-optimizer/SKILL.md)

```markdown
---
name: geo-optimizer
version: 1.0.0
description: Otimiza conteúdo para visibilidade em AI Search engines.
dependencies:
  - name: seo-knowledge-base
    version: "^1.0.0"
    load: summary  # Carrega apenas [SUMMARY] por padrão
---

# GEO Optimizer

## COMPOSIÇÃO

> **LOAD CONTEXT**: Carregar `seo-knowledge-base` (seção SUMMARY).
> Se precisar de detalhes específicos, carregar seção [FULL] correspondente.

## INSTRUÇÕES

Você é um especialista em Generative Engine Optimization. Seu objetivo é
transformar texto para maximizar chances de citação por IAs (ChatGPT, Claude,
Perplexity, Google AI Overview).

### Processo de Otimização

1. **Análise Inicial**
   - Verificar conformidade com regras da base carregada
   - Identificar oportunidades de melhoria
   - Se necessário, carregar [FULL] da base para regras detalhadas

2. **Transformações Aplicadas**
   - Inserir estatísticas com fonte (ex: "Segundo [Estudo X], 73% dos...")
   - Converter parágrafos densos em listas estruturadas
   - Adicionar perguntas retóricas (triggers para Answer Engines)
   - Simplificar construções complexas (facilita tokenização)

3. **Validação Final**
   - Re-verificar contra regras E-E-A-T
   - Garantir que citações têm fonte verificável

## OUTPUT
Retornar o texto otimizado em Markdown, precedido por uma lista de mudanças aplicadas.
```

### 5.4 Metadata com Versionamento (geo-optimizer/metadata.json)

```json
{
  "name": "geo-optimizer",
  "version": "1.0.0",
  "description": "Otimiza conteúdo para AI Search engines usando regras GEO.",
  "dependencies": {
    "seo-knowledge-base": "^1.0.0"
  },
  "input_schema": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "Texto a ser otimizado"
      },
      "optimization_level": {
        "type": "string",
        "enum": ["light", "moderate", "aggressive"],
        "default": "moderate"
      }
    },
    "required": ["content"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "optimized_content": { "type": "string" },
      "changes_made": {
        "type": "array",
        "items": { "type": "string" }
      }
    }
  }
}
```

---

## 6. Desafios, Limitações e Estratégias de Mitigação

### 6.1 Custo de Contexto

**O Problema:** Cada composição adiciona tokens. Uma hierarquia A → B → C pode consumir 5-10k tokens apenas em "imports", reduzindo espaço para o trabalho real.

**Estratégias de Mitigação:**

#### A. Progressive Loading por Seções

Skills base definem seções `[SUMMARY]` e `[FULL]`. O agente carrega o sumário por padrão e expande apenas quando necessário:

```markdown
## [SUMMARY]
Visão geral em ~200 tokens.

## [FULL]
Detalhes completos em ~2000 tokens.
```

A skill derivada declara qual nível carregar:

```yaml
dependencies:
  - name: seo-knowledge-base
    load: summary  # ou "full" quando necessário
```

#### B. Lazy Loading Explícito

Instruções condicionais que carregam contexto sob demanda:

```markdown
> **LOAD ON DEMAND**: seo-knowledge-base
> - Carregar "Regras E-E-A-T [FULL]" apenas se analisando autoridade
> - Carregar "Regras GEO [FULL]" apenas se otimizando para AI Search
```

#### C. Compilação de Skills (Build Step)

Para produção, um processo de build que:
1. Resolve todas as dependências
2. Remove redundâncias entre skills
3. Gera uma skill "compilada" otimizada

Você edita modularmente, mas deploya uma versão flat otimizada.

#### D. Cache Semântico

Se o runtime suportar (ex: via MCP), skills base podem ser pré-processadas em embeddings. O agente consulta semanticamente em vez de carregar texto bruto.

---

### 6.2 Resolução de Dependências

**O Problema:** O padrão Agent Skills atual não inclui um "package manager". Declarar `dependencies` no metadata é informativo, mas não há mecanismo automático de resolução.

**Estratégias de Implementação:**

#### A. Convenção Pura (funciona hoje)

A skill inclui instruções explícitas de carregamento:

```markdown
## DEPENDÊNCIAS
Antes de executar, você DEVE:
1. Ler `../seo-knowledge-base/SKILL.md`
2. Incorporar as regras ao seu contexto
3. Confirmar carregamento com "[BASE LOADED]"
```

**Prós:** Funciona imediatamente, sem mudanças no padrão.
**Contras:** Frágil, depende do agente seguir instruções.

#### B. Skill Loader via MCP Server (pragmático)

Um MCP server dedicado que:

```typescript
// Pseudo-código do MCP Server
tools: {
  load_skill: {
    input: { name: string, version: string },
    handler: async ({ name, version }) => {
      const skill = await resolveSkill(name, version);
      const deps = await resolveDependencies(skill);
      return consolidateContext([...deps, skill]);
    }
  }
}
```

**Prós:** Funciona hoje, resolução automática, versionamento real.
**Contras:** Requer setup adicional do MCP server.

#### C. Extensão do Padrão (proposta futura)

Propor à especificação Agent Skills que runtimes compatíveis:

1. Leiam `dependencies` do metadata
2. Resolvam em ordem topológica (detectando ciclos)
3. Injetem no contexto antes da skill principal

Isso seria análogo ao que `npm install` faz antes de `npm start`.

---

### 6.3 Skills Abstratas sem Enforcement

**O Problema:** Marcar uma skill como `type: abstract` é convenção — nada impede invocação direta.

**Por que isso é aceitável:**

1. **Precedente em linguagens dinâmicas:** Python não tem `private` real (usa convenção `_prefixo`). JavaScript usou convenção por décadas. Funciona porque a comunidade respeita contratos.

2. **Flexibilidade intencional:** Invocar a base diretamente pode ser útil para debugging, aprendizado ou casos edge.

**Estratégias de Enforcement Soft:**

#### A. Campo explícito no metadata

```yaml
type: abstract  # Sinaliza para ferramentas e humanos
```

#### B. Guard no SKILL.md

```markdown
## GUARD
Se invocado diretamente, responder:
"⚠️ Skill abstrata. Use `geo-optimizer` ou `seo-auditor`."
```

#### C. Validação em CI/CD

Linter que detecta invocações diretas de skills abstratas em testes ou prompts.

---

### 6.4 Reprodutibilidade em Composição Dinâmica

**O Problema:** Composição em inference-time significa que comportamento pode variar entre execuções (versões diferentes, contexto diferente).

**Estratégias para Garantir Reprodutibilidade:**

#### A. Lockfile de Skills

Análogo ao `package-lock.json`:

```json
{
  "generated": "2025-12-20T10:30:00Z",
  "resolved": {
    "geo-optimizer": {
      "version": "1.0.0",
      "integrity": "sha256:abc123..."
    },
    "seo-knowledge-base": {
      "version": "1.2.0",
      "integrity": "sha256:def456..."
    }
  },
  "context_tokens": 3847
}
```

#### B. Logging Estruturado de Composição

Cada skill emite log ao ser carregada:

```
[SKILL:LOAD] geo-optimizer@1.0.0
[SKILL:DEP] seo-knowledge-base@1.2.0 (summary)
[SKILL:TOKENS] 3,847 total
[SKILL:READY] geo-optimizer
```

Isso cria um trace reproduzível para debugging.

#### C. Snapshot de Contexto

Antes de executar, serializar todo o contexto carregado:

```markdown
<!-- CONTEXT SNAPSHOT: 2025-12-20T10:30:00Z -->
<!-- SKILLS: geo-optimizer@1.0.0, seo-knowledge-base@1.2.0 -->
<!-- TOKENS: 3847 -->
```

#### D. Contract Testing

Inspirado em Pact (microservices):
- Skills base definem assertions que derivadas devem passar
- CI roda testes quando qualquer skill muda
- Quebras de contrato bloqueiam deploy

---

### 6.5 Dependências Circulares

**O Problema:** Se A carrega B que carrega A, há risco de loop infinito.

**Mitigação:**
- **Convenção:** Skills `type: abstract` nunca carregam outras skills
- **Validação:** Linter que detecta ciclos no grafo de dependências
- **Runtime:** Loader mantém set de "já carregados" e ignora duplicatas

---

### 6.6 Debugging sem Stack Traces

**O Problema:** Diferente de código, não há stack trace quando composição falha.

**Mitigação:**
- Instruções explícitas de confirmação: "Ao carregar X, emita `[X LOADED]`"
- Modo verbose em skills: `debug: true` no metadata habilita outputs extras
- Ferramenta de visualização do grafo de composição

---

## 7. Relação com Model Context Protocol (MCP)

Agent Skills e MCP são complementares:

| Aspecto | Agent Skills | MCP |
|---------|--------------|-----|
| Função | Conhecimento procedural | Conectividade com ferramentas |
| Analogia | Classes/Métodos | APIs/SDKs |
| Exemplo | "Como analisar SEO" | "Conectar ao Google Search Console" |

Uma arquitetura madura usa ambos: **Skills definem o que fazer, MCP provê os meios para fazer**.

O `seo-auditor` pode usar um MCP server para acessar dados reais de crawling, enquanto aplica as regras definidas na `seo-knowledge-base`.

### 7.1 Skill Loader como MCP Server

Uma aplicação prática da sinergia: implementar resolução de dependências como MCP server:

```typescript
const skillLoaderServer = {
  name: "skill-loader",
  tools: {
    load_skill: {
      description: "Carrega uma skill com suas dependências resolvidas",
      input_schema: {
        type: "object",
        properties: {
          name: { type: "string" },
          version: { type: "string" },
          load_level: { enum: ["summary", "full"], default: "summary" }
        }
      }
    },
    list_skills: {
      description: "Lista skills disponíveis e suas dependências"
    },
    validate_dependencies: {
      description: "Verifica se há ciclos ou conflitos de versão"
    }
  }
};
```

---

## 8. Case Study: Content Engine — Degradação sob Composição Multi-Skill

Para demonstrar que os problemas descritos neste paper não são teóricos, apresentamos um caso real de falha em um sistema de produção que segue boas práticas do guia oficial da Anthropic mas carece dos mecanismos arquiteturais propostos aqui.

### 8.1 O Sistema

O *Content Engine* é um sistema de produção de conteúdo multiplataforma operado por um agente Claude. Dado um tema, o sistema transforma esse tema em conteúdo pronto para 5 plataformas simultaneamente: LinkedIn, X/Twitter, Instagram Carrossel, Instagram Reels e YouTube.

A arquitetura segue o padrão orquestrador → especialistas:

```
┌─────────────────────────────────────────┐
│           content-engine                │
│          (Orquestrador)                 │
└──┬──────┬──────┬──────┬──────┬──────────┘
   │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼
┌──────┐┌────┐┌──────┐┌─────┐┌───────┐
│Linked││ X  ││Carros││Reels││YouTube│
│  In  ││    ││  sel ││     ││       │
└──────┘└────┘└──────┘└─────┘└───────┘
   │      │      │      │      │
   └──────┴──────┴──────┴──────┘
                 │
                 ▼
        ┌────────────────┐
        │research-valida-│
        │     tor        │
        │  (Validação)   │
        └────────────────┘
```

Cada plataforma possui uma SKILL.md dedicada com instruções específicas de formato, tom, estrutura e output. A skill de Instagram Carrossel é a mais complexa: exige 7-10 slides em formato tweet-simulado, com anotações visuais por slide ([VISUAL:], [SCREENSHOT:], [IMAGEM:]), números grandes como âncora visual, e uma tabela de guia de produção para o designer.

### 8.2 O Problema Observado

Na execução do tema *"O Segredo dos Agentes de IA: Como Eles Vão Mudar Tudo em 2026"*, o agente carregou todas as 5 skills de plataforma simultaneamente e produziu os 5 outputs em paralelo.

**Resultado:** Quatro dos cinco outputs atingiram a qualidade esperada. O Instagram Carrossel — a skill mais instruction-heavy do sistema — sofreu degradação significativa:

| Critério | Execução Anterior (Boa) | Execução Degradada |
|----------|------------------------|--------------------|
| Slides | 10, com visual directions | 8, texto genérico |
| Anotações visuais | [VISUAL:], [SCREENSHOT:], [IMAGEM:] por slide | Nenhuma |
| Screenshots reais | 3 sugestões específicas | 0 |
| Infográficos Canva | 4 direções detalhadas | 0 |
| Guia de produção | Tabela completa com specs | Ausente |
| Números grandes | Destaque em cada slide | Diluídos no texto |

A execução anterior, para um tema diferente, havia seguido a mesma SKILL.md e produzido output de alta qualidade. A skill não mudou entre as execuções. O que mudou foi o **contexto disponível**: na execução degradada, 5 skills competiam pelos mesmos tokens.

### 8.3 Diagnóstico: Por Que o Guia Oficial Não Bastou

O sistema seguia as boas práticas do guia da Anthropic: skills bem estruturadas, instruções claras, exemplos concretos, progressive disclosure. Mas o guia não aborda o que acontece quando múltiplas skills são carregadas simultaneamente. O agente, sob pressão de contexto, aplicou uma heurística implícita: **"achatar" a skill mais complexa para caber no budget disponível**.

Isso produziu um trade-off invisível: as skills mais simples (LinkedIn, X) saíram intactas porque suas instruções são compactas. A skill mais rica em instruções (Carrossel) foi a que pagou o preço — exatamente o oposto do desejável, já que é a que mais precisa de fidelidade.

### 8.4 Como Esta Arquitetura Resolveria

Cada mecanismo proposto neste paper endereça uma parte do problema:

**Progressive Loading (Seção 6.1):** Em vez de carregar 5 skills inteiras simultaneamente, o orquestrador carregaria [SUMMARY] de cada uma, produziria sequencialmente, e carregaria [FULL] apenas da skill ativa. A skill de Carrossel receberia 100% do contexto quando fosse sua vez.

**Contract Testing (Seção 6.4-D):** A skill definiria assertions obrigatórias:
```markdown
## CONTRACT
Output DEVE conter:
- [ ] Mínimo 7 slides, máximo 10
- [ ] Cada slide com pelo menos uma anotação [VISUAL:], [SCREENSHOT:] ou [IMAGEM:]
- [ ] Pelo menos 2 sugestões de screenshot real
- [ ] Tabela de guia de produção ao final
- [ ] Números/dados destacados em pelo menos 5 slides
```

O agente verificaria esses critérios antes de salvar o output. Se falhasse, recarregaria a skill [FULL] e refaria.

**Context Budget (Seção 6.1-A + Apêndice C):** O lockfile estimaria tokens por skill. O orquestrador saberia antecipadamente que carregar 5 skills simultaneamente excede o budget e optaria por execução sequencial.

**Logging Estruturado (Seção 6.4-B + Apêndice D):** Traces de composição revelariam que a skill de Carrossel foi carregada em modo reduzido, tornando o problema visível em vez de silencioso.

### 8.5 Lição Aprendida

O caso demonstra que **a qualidade de um sistema de skills é limitada não pela qualidade das skills individuais, mas pela capacidade do sistema de compô-las sem degradação**. Skills excelentes produzem outputs medíocres quando o mecanismo de composição é ingênuo.

O guia da Anthropic cria as condições necessárias (skills bem escritas), mas não suficientes (composição gerenciada). A arquitetura proposta neste paper fornece a camada que transforma skills individuais em sistemas confiáveis.

---

## 9. Trabalhos Futuros

1. **Skill Discovery Protocol:** Mecanismo para Skills se auto-registrarem e anunciarem capacidades/dependências em um registry.

2. **Skill Testing Framework:** Testes automatizados para validar compatibilidade entre skills (LSP enforcement via contract tests).

3. **Skill Marketplace com Hierarquias:** Repositório comunitário que entende e visualiza relações de dependência entre skills.

4. **Auto-geração de Skills:** Agentes que observam workflows e geram skills automaticamente, identificando abstrações comuns.

5. **Compilador de Skills:** Ferramenta que recebe um grafo de skills e gera versão otimizada para produção.

6. **Métricas de Composição:** Dashboard que mostra custo de tokens por skill, frequência de uso, e sugere otimizações.

---

## 10. Conclusão

A publicação do guia oficial da Anthropic (Ref. 4) validou os fundamentos: skills bem estruturadas com progressive disclosure, instruções claras e exemplos concretos são a base de qualquer sistema de agentes. Porém, como o case study da Seção 8 demonstrou empiricamente, **skills individuais de qualidade não garantem resultados de qualidade quando compostas**. A degradação silenciosa sob carga multi-skill é um problema real que o guia oficial não endereça.

Este paper propõe a camada arquitetural complementar. Ao tratar Skills como objetos composíveis e aplicar princípios SOLID, podemos construir sistemas de agentes que são:

- **Manuteníveis:** Mudanças propagam corretamente através de contratos bem definidos.
- **Escaláveis:** Novas capacidades são adições, não reescritas.
- **Testáveis:** Componentes isolados podem ser validados independentemente via contract testing.
- **Reutilizáveis:** Conhecimento vive em um lugar, usado em muitos.
- **Reproduzíveis:** Lockfiles e logging estruturado garantem consistência.
- **Resilientes:** Context budgets e validation gates previnem degradação silenciosa.

Os desafios de custo de contexto, resolução de dependências e reprodutibilidade são reais, mas tratáveis com as estratégias apresentadas — muitas funcionando hoje, sem mudanças no padrão. O caso do Content Engine prova que essas estratégias não são otimizações teóricas: são requisitos práticos para qualquer sistema que compõe mais de duas skills simultaneamente.

Esta proposta não requer alterações na especificação Agent Skills — é uma convenção de design e conjunto de práticas que funcionam com o padrão atual, posicionando-se como extensão natural do guia oficial. Esperamos que a comunidade expanda essas ideias e contribua para um ecossistema de Skills verdadeiramente modular.

O repositório que acompanha este paper inclui um **modo de demonstração** (`--demo`) que executa os três orchestrators com dados de exemplo. A resolução de dependências, composição de contexto e logging estruturado são reais — permitindo verificar em segundos que a arquitetura proposta funciona como descrito, sem necessidade de API keys ou dependências externas. Um modo de execução via API (`--run`) também está disponível para validação com modelos reais.

---

## Referências

### Agent Skills e AI Agents
1. Anthropic. "Agent Skills Specification." agentskills.io, 2025.
2. Anthropic. "Equipping agents for the real world with Agent Skills." anthropic.com/engineering, 2025.
3. Anthropic. "Model Context Protocol." modelcontextprotocol.io, 2024.
4. Anthropic. "The Complete Guide to Building Skills for Claude." 2026.

### Engenharia de Software e Design Patterns
5. Gamma, E. et al. "Design Patterns: Elements of Reusable Object-Oriented Software." Addison-Wesley, 1994.
6. Martin, R. C. "Clean Architecture." Prentice Hall, 2017.
7. Martin, R. C. "The SOLID Principles of Object-Oriented Design." butunclebob.com, 2000.

### Segurança de Software (Domínio Code Review)
8. OWASP Foundation. "OWASP Top Ten 2021." owasp.org/Top10, 2021.
9. MITRE Corporation. "CWE Top 25 Most Dangerous Software Weaknesses." cwe.mitre.org, 2023.
10. NIST. "Secure Software Development Framework (SSDF)." csrc.nist.gov, 2022.

### Finanças e Gestão de Risco (Domínio Investment Analysis)
11. Markowitz, H. "Portfolio Selection." The Journal of Finance, 1952.
12. Sharpe, W. F. "The Sharpe Ratio." The Journal of Portfolio Management, 1994.
13. Jorion, P. "Value at Risk: The New Benchmark for Managing Financial Risk." McGraw-Hill, 2006.
14. CFA Institute. "Global Investment Performance Standards (GIPS)." cfainstitute.org, 2020.

---

## Apêndice A: Checklist de Revisão para Skills Hierárquicas

- [ ] Cada Skill tem uma única responsabilidade?
- [ ] Skills base são marcadas como `type: abstract`?
- [ ] Skills base incluem `[SUMMARY]` e `[FULL]` para progressive loading?
- [ ] Dependências estão declaradas no metadata.json?
- [ ] Versionamento semântico está sendo usado?
- [ ] Skills derivadas podem substituir bases sem quebrar fluxos?
- [ ] Guards estão implementados em skills abstratas?
- [ ] Há logging estruturado para debugging?
- [ ] Lockfile é gerado para ambientes de produção?
- [ ] Testes de contrato validam composição?

---

## Apêndice B: Especificação do Formato [SUMMARY]/[FULL]

### Propósito

Permitir progressive loading de contexto dentro de uma única skill, reduzindo consumo de tokens quando detalhes completos não são necessários.

### Sintaxe

```markdown
## [SUMMARY]
Conteúdo conciso (~10-20% do tamanho total).
Deve ser auto-contido para casos simples.

## [FULL]
Conteúdo completo com todos os detalhes.
Pode referenciar o SUMMARY ou ser independente.
```

### Regras

1. `[SUMMARY]` deve sempre vir antes de `[FULL]`
2. `[SUMMARY]` deve ser suficiente para 80% dos casos de uso
3. `[FULL]` pode ser dividido em subseções: `[FULL:topico]`
4. Skills que dependem podem especificar qual nível carregar:

```yaml
dependencies:
  - name: base-skill
    load: summary  # "summary" | "full" | "full:topico"
```

### Exemplo de Carregamento Condicional

```markdown
> **LOAD CONTEXT**: base-skill (summary)
>
> Se a tarefa envolver [caso específico], carregar também:
> `base-skill [FULL:caso-especifico]`
```

---

## Apêndice C: Exemplo de Lockfile de Skills

```json
{
  "$schema": "https://agentskills.io/schemas/lockfile-v1.json",
  "generated": "2025-12-20T10:30:00Z",
  "generator": "skill-loader@1.0.0",

  "root": "content-orchestrator",

  "resolved": {
    "content-orchestrator": {
      "version": "2.1.0",
      "path": "./skills/content-orchestrator",
      "integrity": "sha256:a1b2c3d4...",
      "dependencies": ["geo-optimizer", "seo-auditor", "content-writer"]
    },
    "geo-optimizer": {
      "version": "1.0.0",
      "path": "./skills/geo-optimizer",
      "integrity": "sha256:e5f6g7h8...",
      "dependencies": ["seo-knowledge-base"],
      "load_level": "summary"
    },
    "seo-auditor": {
      "version": "1.3.0",
      "path": "./skills/seo-auditor",
      "integrity": "sha256:i9j0k1l2...",
      "dependencies": ["seo-knowledge-base"],
      "load_level": "full"
    },
    "content-writer": {
      "version": "1.1.0",
      "path": "./skills/content-writer",
      "integrity": "sha256:m3n4o5p6...",
      "dependencies": ["seo-knowledge-base"],
      "load_level": "summary"
    },
    "seo-knowledge-base": {
      "version": "1.2.0",
      "path": "./skills/seo-knowledge-base",
      "integrity": "sha256:q7r8s9t0...",
      "dependencies": [],
      "type": "abstract"
    }
  },

  "context_budget": {
    "total_tokens": 8420,
    "by_skill": {
      "content-orchestrator": 1200,
      "geo-optimizer": 850,
      "seo-auditor": 2100,
      "content-writer": 920,
      "seo-knowledge-base:summary": 480,
      "seo-knowledge-base:full": 2870
    }
  },

  "composition_order": [
    "seo-knowledge-base",
    "geo-optimizer",
    "seo-auditor",
    "content-writer",
    "content-orchestrator"
  ]
}
```

### Campos do Lockfile

| Campo | Descrição |
|-------|-----------|
| `generated` | Timestamp de geração |
| `root` | Skill principal sendo executada |
| `resolved` | Mapa de todas as skills com versões exatas |
| `integrity` | Hash do conteúdo para verificação |
| `load_level` | Nível de carregamento usado (summary/full) |
| `context_budget` | Estimativa de tokens por skill |
| `composition_order` | Ordem topológica de carregamento |

---

## Apêndice D: Template de Logging Estruturado

```markdown
<!-- SKILL COMPOSITION LOG -->
<!-- Generated: 2025-12-20T10:30:00Z -->

[COMPOSE:START] content-orchestrator@2.1.0
  [DEP:RESOLVE] geo-optimizer@1.0.0
    [DEP:RESOLVE] seo-knowledge-base@1.2.0 (summary)
    [DEP:LOADED] seo-knowledge-base@1.2.0 [480 tokens]
  [DEP:LOADED] geo-optimizer@1.0.0 [1330 tokens]
  [DEP:RESOLVE] seo-auditor@1.3.0
    [DEP:CACHED] seo-knowledge-base@1.2.0 (full, upgrading from summary)
    [DEP:LOADED] seo-knowledge-base@1.2.0 [+2390 tokens]
  [DEP:LOADED] seo-auditor@1.3.0 [4490 tokens]
  [DEP:RESOLVE] content-writer@1.1.0
    [DEP:CACHED] seo-knowledge-base@1.2.0 (summary, already have full)
  [DEP:LOADED] content-writer@1.1.0 [920 tokens]
[COMPOSE:LOADED] content-orchestrator@2.1.0 [1200 tokens]
[COMPOSE:COMPLETE] Total: 8420 tokens | Skills: 5 | Time: 127ms
```

---

*Paper disponível em: https://github.com/gugastork/agente-skill-oop/blob/main/PAPER.md*
*Implementação de referência: https://github.com/gugastork/agente-skill-oop*
