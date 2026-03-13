# Agent Skills Orientadas a Objetos: Arquitetura Modular para Agentes de IA Escaláveis

**Autor:** Gustavo Stork  
**Data:** 20 de Dezembro de 2025  
**Versão:** 4.0

---

## Resumo

Os agentes de IA atuais sofrem de um problema estrutural: prompts monolíticos que consomem contexto desnecessariamente e resistem à manutenção. Com a abertura do padrão Agent Skills pela Anthropic (18/Dez/2025), surge a oportunidade de aplicar décadas de aprendizado em Engenharia de Software ao design de agentes.

Este paper propõe tratar Skills como **objetos comportamentais**: unidades encapsuladas que podem ser compostas hierarquicamente, seguindo princípios SOLID. Demonstramos a viabilidade através de um sistema de otimização SEO/GEO com quatro camadas de abstração, apresentamos estratégias concretas para mitigar custos de contexto e propomos mecanismos de resolução de dependências compatíveis com o padrão atual.

**Palavras-chave:** Agent Skills, OOP, SOLID, Prompt Engineering, AI Agents, Composição, Modularidade

---

## 1. Introdução

### 1.1 O Problema

System prompts tradicionais operam como **variáveis globais**: sempre presentes, sempre consumindo tokens, impossíveis de modularizar. À medida que agentes ganham capacidades, esses prompts crescem até se tornarem ingerenciáveis.

Agent Skills resolvem parte do problema através de *progressive disclosure* — carregamento sob demanda. Porém, o padrão atual é **plano**: Skills são independentes, sem mecanismos nativos para expressar dependências ou hierarquias.

### 1.2 A Proposta

Argumentamos que Skills podem — e devem — ser tratadas como **classes** em Programação Orientada a Objetos:

- **Encapsulamento**: Cada Skill isola seu conhecimento e comportamento
- **Composição**: Skills complexas delegam para Skills especializadas
- **Abstração**: Skills "base" definem contratos que derivadas implementam
- **Reutilização**: Conhecimento compartilhado vive em um único lugar (DRY)

> **Nota sobre terminologia**: Usamos "herança" metaforicamente. Tecnicamente, o mecanismo é *composição* — uma Skill carrega outra em seu contexto. Argumentamos que isso é *preferível* à herança verdadeira, alinhando-se ao princípio "favor composition over inheritance" do Gang of Four.

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

> *Uma Skill deve ter apenas uma razão para mudar.*

**Anti-pattern**: Uma Skill que "analisa SEO, reescreve conteúdo e publica no CMS".

**Pattern correto**: 
- `seo-auditor` → apenas análise
- `content-writer` → apenas escrita
- `cms-publisher` → apenas publicação

### O — Open/Closed Principle

> *Skills devem estar abertas para extensão, fechadas para modificação.*

A `seo-knowledge-base` pode receber novas regras (extensão) sem que o `geo-optimizer` precise ser alterado (fechado). O optimizer simplesmente carrega a base atualizada.

### L — Liskov Substitution Principle

> *Skills derivadas devem ser substituíveis por suas bases.*

Se um fluxo espera um "otimizador de texto", tanto `seo-optimizer` quanto `geo-optimizer` devem funcionar — ambos aceitam texto e retornam texto otimizado, apenas com estratégias diferentes.

### I — Interface Segregation Principle

> *Muitas interfaces específicas são melhores que uma interface geral.*

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

> *Dependa de abstrações, não de implementações.*

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
│(Especialização)│ │(Especialização)│ │  (Gerador)    │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └────────────┬────┴─────────────────┘
                     │
                     ▼
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
| **Abstração** | `seo-knowledge-base` | Regras E-E-A-T, Core Web Vitals, diretrizes GEO. Nunca executa, apenas define. |
| **Especialização** | `geo-optimizer` | Transforma texto para otimização em AI Search. Carrega a base. |
| **Utilitário** | `seo-auditor` | Valida conformidade contra a base. Retorna score + sugestões. |
| **Orquestração** | `content-orchestrator` | Coordena o fluxo: gerar → auditar → otimizar → validar. |

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

### 5.2 Skill Base com Progressive Loading

Veja a implementação completa em `/skills/seo-knowledge-base/SKILL.md`. Características principais:

- **GUARD**: Previne invocação direta
- **[SUMMARY]**: ~200 tokens para casos simples
- **[FULL]**: Detalhes completos quando necessário
- **[ABSTRACT]**: Métodos que derivadas devem implementar

### 5.3 Convenções de Composição

Para uma skill "herdar" de outra:

```markdown
## COMPOSIÇÃO

> **LOAD CONTEXT**: Carregar `seo-knowledge-base` (seção SUMMARY).
> Se precisar de detalhes específicos, carregar seção [FULL] correspondente.
```

### 5.4 Metadata com Dependências

```json
{
  "dependencies": {
    "seo-knowledge-base": {
      "version": "^1.0.0",
      "load": "summary"
    }
  }
}
```

---

## 6. Desafios, Limitações e Estratégias de Mitigação

### 6.1 Custo de Contexto

**O Problema**: Cada composição adiciona tokens. Uma hierarquia A → B → C pode consumir 5-10k tokens apenas em "imports".

**Estratégias de Mitigação:**

| Estratégia | Descrição | Funciona Hoje? |
|------------|-----------|----------------|
| Progressive Loading | Seções `[SUMMARY]` e `[FULL]` | ✅ Sim |
| Lazy Loading | Carregar sob demanda via instruções | ✅ Sim |
| Compilação | Build step que gera skill flat | ✅ Sim |
| Cache Semântico | Embeddings via MCP | ⚠️ Requer infra |

### 6.2 Resolução de Dependências

**O Problema**: Não há "package manager" nativo.

**Estratégias:**

| Estratégia | Prós | Contras |
|------------|------|---------|
| Convenção Pura | Funciona hoje | Frágil |
| MCP Server | Automático, versionado | Requer setup |
| Extensão do Padrão | Ideal | Futuro |

### 6.3 Skills Abstratas sem Enforcement

**Por que convenção funciona**: Python não tem `private` real. JavaScript usou convenção por décadas. A comunidade respeita contratos.

**Enforcement Soft**:
- Campo `type: abstract` no metadata
- GUARD no SKILL.md
- Linter em CI/CD

### 6.4 Reprodutibilidade

**Soluções propostas**:
- **Lockfile**: Versões exatas + hashes (Apêndice C)
- **Logging Estruturado**: Trace de composição (Apêndice D)
- **Contract Testing**: Validação automática de compatibilidade

### 6.5 Dependências Circulares

**Mitigação**: Skills abstratas nunca carregam outras skills + validação no loader.

### 6.6 Debugging

**Mitigação**: Confirmações explícitas (`[X LOADED]`) + modo verbose + visualização de grafo.

---

## 7. Relação com Model Context Protocol (MCP)

| Aspecto | Agent Skills | MCP |
|---------|--------------|-----|
| **Função** | Conhecimento procedural | Conectividade com ferramentas |
| **Analogia** | Classes/Métodos | APIs/SDKs |
| **Exemplo** | "Como analisar SEO" | "Conectar ao Google Search Console" |

### 7.1 Skill Loader como MCP Server

```typescript
const skillLoaderServer = {
  name: "skill-loader",
  tools: {
    load_skill: {
      description: "Carrega uma skill com suas dependências resolvidas",
      input_schema: {
        properties: {
          name: { type: "string" },
          version: { type: "string" },
          load_level: { enum: ["summary", "full"], default: "summary" }
        }
      }
    },
    validate_dependencies: {
      description: "Verifica se há ciclos ou conflitos de versão"
    }
  }
};
```

---

## 8. Trabalhos Futuros

1. **Skill Discovery Protocol**: Registry para auto-registro de capabilities
2. **Skill Testing Framework**: Contract tests para LSP enforcement
3. **Skill Marketplace**: Repositório com visualização de hierarquias
4. **Auto-geração de Skills**: Agentes que identificam abstrações comuns
5. **Compilador de Skills**: Otimização para produção
6. **Métricas de Composição**: Dashboard de tokens/uso

---

## 9. Conclusão

A transformação de Agent Skills em padrão aberto cria uma oportunidade única para aplicar décadas de aprendizado em Engenharia de Software ao design de agentes de IA. Ao tratar Skills como objetos composíveis e aplicar princípios SOLID, podemos construir sistemas de agentes que são:

- **Manuteníveis**: Mudanças propagam corretamente através de contratos bem definidos
- **Escaláveis**: Novas capacidades são adições, não reescritas
- **Testáveis**: Componentes isolados podem ser validados independentemente
- **Reutilizáveis**: Conhecimento vive em um lugar, usado em muitos
- **Reproduzíveis**: Lockfiles e logging estruturado garantem consistência

Os desafios de custo de contexto, resolução de dependências e reprodutibilidade são reais, mas tratáveis com as estratégias apresentadas — muitas funcionando hoje, sem mudanças no padrão.

Esta proposta não requer alterações na especificação Agent Skills — é uma convenção de design e conjunto de práticas que funcionam com o padrão atual.

---

## Referências

1. Anthropic. "Agent Skills Specification." agentskills.io, 2025.
2. Anthropic. "Equipping agents for the real world with Agent Skills." anthropic.com/engineering, 2025.
3. Gamma, E. et al. "Design Patterns: Elements of Reusable Object-Oriented Software." Addison-Wesley, 1994.
4. Martin, R. C. "Clean Architecture." Prentice Hall, 2017.
5. Martin, R. C. "Agile Software Development, Principles, Patterns, and Practices." Prentice Hall, 2002.
6. Anthropic. "Model Context Protocol." modelcontextprotocol.io, 2024.

---

## Apêndice A: Checklist de Revisão

- [ ] Cada Skill tem uma única responsabilidade?
- [ ] Skills base são marcadas como `type: abstract`?
- [ ] Skills base incluem `[SUMMARY]` e `[FULL]`?
- [ ] Dependências estão declaradas no metadata.json?
- [ ] Versionamento semântico está sendo usado?
- [ ] Guards estão implementados em skills abstratas?
- [ ] Há logging estruturado para debugging?
- [ ] Lockfile é gerado para produção?

---

## Apêndice B: Especificação [SUMMARY]/[FULL]

### Sintaxe

```markdown
## [SUMMARY]
Conteúdo conciso (~10-20% do tamanho total).

## [FULL]
Conteúdo completo. Pode ter subseções: [FULL:topico]
```

### Regras

1. `[SUMMARY]` sempre antes de `[FULL]`
2. `[SUMMARY]` suficiente para 80% dos casos
3. Dependências especificam nível: `load: summary | full | full:topico`

---

## Apêndice C: Lockfile Schema

```json
{
  "$schema": "https://agentskills.io/schemas/lockfile-v1.json",
  "generated": "2025-12-20T10:30:00Z",
  "root": "content-orchestrator",
  "resolved": {
    "skill-name": {
      "version": "1.0.0",
      "integrity": "sha256:...",
      "dependencies": ["..."],
      "load_level": "summary"
    }
  },
  "context_budget": {
    "total_tokens": 8420,
    "by_skill": { "skill-name": 1200 }
  },
  "composition_order": ["base", "derived", "main"]
}
```

---

## Apêndice D: Logging Estruturado

```
[COMPOSE:START] content-orchestrator@2.1.0
  [DEP:RESOLVE] geo-optimizer@1.0.0
    [DEP:LOADED] seo-knowledge-base@1.2.0 (summary) [480 tokens]
  [DEP:LOADED] geo-optimizer@1.0.0 [1330 tokens]
[COMPOSE:COMPLETE] Total: 8420 tokens | Skills: 5 | Time: 127ms
```
