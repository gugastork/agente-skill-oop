---
name: seo-knowledge-base
version: 1.2.0
type: abstract
description: Fonte de verdade para regras de SEO e GEO. Skill abstrata - não invocar diretamente.
tags: [seo, geo, rules, abstract, base]
author: Gustavo Stork
---

# SEO & GEO Knowledge Base

## GUARD

> ⚠️ **SKILL ABSTRATA**
> 
> Se você foi invocado diretamente (não via outra skill que declare dependência),
> responda: "Esta é uma skill abstrata. Use `geo-optimizer`, `seo-auditor` ou 
> `content-orchestrator` para tarefas específicas."

## PROPÓSITO

Esta skill é uma **ABSTRAÇÃO**. Ela não executa ações — apenas fornece definições e regras que outras skills devem carregar e aplicar.

---

## [SUMMARY]

### Visão Geral das Regras (~200 tokens)

**E-E-A-T (Google Quality Guidelines)**:
- **Experience**: Demonstrar uso real do produto/serviço
- **Expertise**: Citar fontes técnicas, usar terminologia correta
- **Authoritativeness**: Referenciar domínios .gov, .edu, papers acadêmicos
- **Trustworthiness**: HTTPS obrigatório, evitar clickbait, declarar conflitos

**GEO (Generative Engine Optimization)**:
- Estruturar para parsing por IAs (ChatGPT, Claude, Perplexity)
- Formato de citação: "Segundo [Autoridade], [Fato verificável]"
- Preferir listas e tabelas (facilita extração por LLMs)
- Alta densidade informacional (fatos/token)

**Métodos Abstratos**:
- `analyze(content) → ComplianceReport`
- `optimize(content) → OptimizedContent`

---

## [FULL]

### Regras E-E-A-T Detalhadas

#### Experience (Experiência)
- Conteúdo deve demonstrar uso real do produto/serviço
- Incluir casos de uso específicos, não apenas teoria
- Evitar generalidades; preferir exemplos concretos
- Mostrar resultados mensuráveis quando possível

#### Expertise (Especialização)
- Citar fontes técnicas verificáveis
- Usar terminologia correta do domínio
- Demonstrar profundidade de conhecimento
- Incluir nuances que apenas especialistas conheceriam

#### Authoritativeness (Autoridade)
- Referenciar domínios de alta autoridade (.gov, .edu, papers)
- Evitar fontes anônimas ou não verificáveis
- Incluir credenciais do autor quando relevante
- Preferir estudos primários a agregadores

#### Trustworthiness (Confiabilidade)
- HTTPS obrigatório para todos os links
- Evitar táticas de clickbait no título e corpo
- Declarar conflitos de interesse quando aplicável
- Manter consistência factual ao longo do conteúdo

---

### [FULL:geo]

#### Estrutura para AI Parsing
- Usar formato: "Segundo [Autoridade], [Fato verificável]"
- Preferir listas e tabelas (facilita extração por LLMs)
- Manter alta densidade informacional (fatos/token)
- Evitar ambiguidade; ser preciso e específico
- Cada parágrafo deve fazer sentido isoladamente

#### Otimização de Citação
- IAs priorizam conteúdo que pode ser citado com atribuição clara
- Incluir estatísticas com fonte e data
- Formato ideal: "[Métrica] segundo [Fonte] ([Ano])"

**Exemplo**:
```
✅ BOM: "Segundo o MIT (2024), 73% dos modelos de linguagem..."
❌ RUIM: "Muitos especialistas dizem que a maioria dos modelos..."
```

#### Triggers para Answer Engines
- Perguntas retóricas aumentam chance de match com queries
- Headers em formato de pergunta (H2, H3) são indexados como FAQs
- Listas numeradas são preferidas para "how-to" content

---

### [FULL:technical]

#### Core Web Vitals (Referência)

| Métrica | Bom | Precisa Melhorar | Ruim |
|---------|-----|------------------|------|
| LCP (Largest Contentful Paint) | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| INP (Interaction to Next Paint) | ≤ 200ms | ≤ 500ms | > 500ms |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | ≤ 0.25 | > 0.25 |

#### Checklist Técnico SEO

**Obrigatório:**
- [ ] Título com keyword principal (primeiros 60 caracteres)
- [ ] Meta description com CTA (até 155 caracteres)
- [ ] H1 único por página
- [ ] Alt text em todas as imagens
- [ ] Links internos relevantes (mínimo 2-3)

**Recomendado:**
- [ ] Structured data (JSON-LD) quando aplicável
- [ ] Table of contents para conteúdo > 1500 palavras
- [ ] FAQ section com schema markup
- [ ] Autor identificado com credentials

---

## [ABSTRACT] Métodos a Implementar

Skills que "herdam" desta base devem implementar:

```
analyze(content: string) → ComplianceReport
  - Recebe texto
  - Retorna relatório de conformidade com score 0-100
  - Deve verificar E-E-A-T e GEO

optimize(content: string, level: "light" | "moderate" | "aggressive") → OptimizedContent
  - Recebe texto e nível de otimização
  - Retorna texto otimizado + lista de mudanças
  
validate(content: string, rules: string[]) → ValidationResult
  - Recebe texto e lista de regras específicas
  - Retorna resultado de validação por regra
```

---

## CHANGELOG

- **v1.2.0** (2025-12-20): Adicionado formato [SUMMARY]/[FULL], GUARD, INP metric
- **v1.1.0** (2025-12-15): Adicionado seção de Core Web Vitals
- **v1.0.0** (2025-12-10): Versão inicial com E-E-A-T e GEO básico
