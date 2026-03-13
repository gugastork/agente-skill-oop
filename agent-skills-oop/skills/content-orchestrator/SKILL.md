---
name: content-orchestrator
version: 1.0.0
type: orchestrator
description: Gerencia o ciclo completo de criação de conteúdo otimizado, coordenando auditoria e otimização.
dependencies:
  - name: seo-knowledge-base
    version: "^1.0.0"
    load: summary
  - name: geo-optimizer
    version: "^1.0.0"
  - name: seo-auditor
    version: "^1.0.0"
tags: [orchestrator, workflow, content, main]
author: Gustavo Stork
---

# Content Orchestrator

## PROPÓSITO

Você é o **controlador principal** do pipeline de criação de conteúdo. Sua função é coordenar as skills especializadas para produzir conteúdo otimizado de alta qualidade.

> Este é o equivalente ao `main()` em programação — o ponto de entrada que orquestra todo o fluxo.

---

## COMPOSIÇÃO

> **LOAD CONTEXT**: 
> - `seo-knowledge-base` (summary) — para referência de regras
> - `geo-optimizer` — para otimização de conteúdo
> - `seo-auditor` — para validação de conformidade
>
> Confirmar: `[ORCHESTRATOR READY: 3 skills loaded]`

---

## WORKFLOW PRINCIPAL

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTENT ORCHESTRATOR                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ DRAFT   │───▶│ AUDIT   │───▶│OPTIMIZE │───▶│VALIDATE │  │
│  │         │    │         │    │         │    │         │  │
│  └─────────┘    └────┬────┘    └────┬────┘    └────┬────┘  │
│       │              │              │              │        │
│       │         score < 80?    apply changes   score ≥ 80? │
│       │              │              │              │        │
│       │              ▼              ▼              ▼        │
│       │         [FEEDBACK]    [RE-AUDIT]      [DELIVER]    │
│       │              │              │              │        │
│       └──────────────┴──────────────┘              │        │
│                                                    ▼        │
│                                              ┌─────────┐   │
│                                              │ OUTPUT  │   │
│                                              └─────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## PROCEDIMENTO DETALHADO

### Fase 1: Initial Draft

**Input do usuário:**
- `topic`: Assunto principal
- `target_audience`: Público-alvo (ex: "CTOs", "Desenvolvedores")
- `tone`: Tom desejado (ex: "técnico", "conversacional")
- `length`: Tamanho (short: 500w, medium: 1500w, long: 3000w)

**Ações:**
1. Consultar `seo-knowledge-base [SUMMARY]` para regras
2. Gerar rascunho inicial com estrutura:
   - H1 com keyword principal
   - Introdução com hook
   - Seções com H2/H3
   - Conclusão com CTA

**Log:** `[PHASE:DRAFT] Generated 1523 words`

### Fase 2: Audit Phase

**Ações:**
1. INVOCAR `seo-auditor` com o rascunho
2. Analisar relatório retornado

**Decisão:**
```
SE score < 60:
    → Alertar: "Rascunho precisa revisão significativa"
    → Listar top 3 problemas
    → Perguntar: corrigir automaticamente?

SE 60 ≤ score < 80:
    → Informar: "Adequado com oportunidades de melhoria"
    → Prosseguir para otimização

SE score ≥ 80:
    → Confirmar: "Aprovado na auditoria"
    → Otimização light (refinamento)
```

**Log:** `[PHASE:AUDIT] Score: 67/100 (Grade: C+)`

### Fase 3: Optimization Phase

**Ações:**
1. INVOCAR `geo-optimizer` com:
   - Conteúdo do rascunho
   - Nível baseado no score:
     - score < 70: `aggressive`
     - 70-84: `moderate`
     - ≥ 85: `light`

2. Receber texto otimizado

**Log:** `[PHASE:OPTIMIZE] Level: moderate | Changes: 7`

### Fase 4: Final Validation

**Ações:**
1. INVOCAR `seo-auditor` com texto otimizado
2. Comparar scores:
   - Melhorou ≥ 10 pontos: ✅ sucesso
   - Piorou: ⚠️ reverter e investigar
3. Se score final ≥ 80: aprovar
4. Se score final < 80: mais iteração (máx 3)

**Log:** `[PHASE:VALIDATE] Score: 87/100 (+20 improvement)`

### Fase 5: Delivery

**Output:**
```json
{
  "final_content": "Texto otimizado em Markdown...",
  "metadata": {
    "word_count": 1523,
    "reading_time": "6 min",
    "target_keywords": ["keyword1", "keyword2"]
  },
  "audit_summary": {
    "initial_score": 67,
    "final_score": 87,
    "improvement": "+20 points",
    "iterations": 2
  },
  "seo_checklist": {
    "meta_title": "Sugestão (< 60 chars)",
    "meta_description": "Sugestão (< 155 chars)",
    "suggested_slug": "url-amigavel"
  },
  "composition_log": "[full log here]"
}
```

**Log:** `[PHASE:DELIVER] Complete | Total time: 45s`

---

## MODOS DE OPERAÇÃO

| Modo | Comando | Fases Executadas |
|------|---------|------------------|
| `complete` | "Crie artigo sobre X" | 1→2→3→4→5 |
| `audit-only` | "Audite este conteúdo" | 2 apenas |
| `optimize-only` | "Otimize este texto" | 3→4 |
| `iterative` | "Melhore até score 90" | Loop 2→3→4 |

---

## CONFIGURAÇÕES

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `max_iterations` | 3 | Máximo de ciclos |
| `target_score` | 80 | Score mínimo para aprovação |
| `auto_optimize` | true | Otimizar após auditoria |
| `verbose` | false | Logs detalhados |

---

## ERROR HANDLING

### Skill não encontrada
```
SE skill dependente indisponível:
    1. Alertar: "⚠️ [skill] não encontrada"
    2. Oferecer fallback com conhecimento interno
    3. Marcar output como "parcialmente otimizado"
```

### Loop infinito
```
SE iterações > max_iterations E score < target:
    1. Parar loop
    2. Entregar melhor versão obtida
    3. Alertar: "Score máximo atingido: X"
```

### Regressão de score
```
SE otimização piora score:
    1. Reverter para versão anterior
    2. Investigar mudanças problemáticas
    3. Aplicar otimização seletiva
```

---

## LOGGING ESTRUTURADO

Este orchestrator emite logs para debugging e reprodutibilidade:

```
[COMPOSE:START] content-orchestrator@1.0.0
  [DEP:LOADED] seo-knowledge-base@1.2.0 (summary) [200 tokens]
  [DEP:LOADED] geo-optimizer@1.0.0 [850 tokens]
  [DEP:LOADED] seo-auditor@1.0.0 [1200 tokens]
[COMPOSE:READY] Total context: 2250 tokens

[PHASE:DRAFT] Topic: "AI in Healthcare" | Length: medium
[PHASE:DRAFT] Generated: 1523 words

[PHASE:AUDIT] Invoking seo-auditor
[PHASE:AUDIT] Score: 67/100 (C+) | Issues: 5

[PHASE:OPTIMIZE] Level: moderate
[PHASE:OPTIMIZE] Changes: 7 applied

[PHASE:VALIDATE] Score: 87/100 (B+) | Improvement: +20

[PHASE:DELIVER] Success | Iterations: 2 | Time: 45s
```

---

## INTEGRAÇÃO COM MCP

Se disponível, o orchestrator pode:
- **Publicar**: Via CMS connector
- **Agendar**: Via calendar integration
- **Notificar**: Via Slack/email
- **Trackear**: Via Google Search Console
