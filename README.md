# Agent Skills OOP

> Applying Object-Oriented Programming principles to the Agent Skills open standard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Open%20Standard-blue)](https://agentskills.io)
[![Version](https://img.shields.io/badge/version-5.0-green)](./PAPER.md)

## The Problem

As AI agents grow more capable, their prompts become **monolithic nightmares**:
- 10k+ tokens always loaded
- Rules copy-pasted across Skills
- No dependency management
- Impossible to test in isolation
- Silent degradation when multiple Skills compete for context

## The Solution

Treat Skills as **composable objects** with OOP principles:

| Principle | Application |
|-----------|-------------|
| **Encapsulation** | Each Skill isolates its knowledge |
| **Composition** | Skills load other Skills dynamically |
| **Abstraction** | Base Skills define contracts |
| **SOLID** | All 5 principles apply to Skill design |

### Relationship with Anthropic's Official Guide

In February 2026, Anthropic published *"The Complete Guide to Building Skills for Claude"* — the first official guide for Agent Skills design. This paper builds on that foundation as the **architectural layer for multi-skill systems in production**:

| Aspect | Anthropic's Guide | This Paper |
|--------|-------------------|------------|
| Scope | Individual skill | System of skills |
| Composition | Mentioned, not mechanized | Hierarchies, contracts, dependency resolution |
| Quality | Writing best practices | Contract testing, validation gates |
| Context | Progressive Disclosure (3 levels) | Progressive Loading ([SUMMARY]/[FULL]) + budget |
| Reproducibility | Not addressed | Lockfiles, structured logging, snapshots |

## Quick Start

```bash
# Clone
git clone https://github.com/gugastork/agente-skill-oop.git
cd agente-skill-oop

# List all 12 skills across 3 domains
python loader.py --list

# SEO/GEO domain
python loader.py content-orchestrator --tree

# Code Review domain
python loader.py code-review-orchestrator --tree

# Finance domain
python loader.py investment-orchestrator --tree

# Generate lockfile for reproducibility
python loader.py content-orchestrator --lockfile

# Compose full context
python loader.py content-orchestrator --compose --output context.md

# Validate all skills
python loader.py --validate
```

## Repository Structure

```
agente-skill-oop/
├── README.md
├── PAPER.md               # Full technical paper (v5.0)
├── MARKETING.md
├── CONTRIBUTING.md
├── LICENSE
├── loader.py              # Python loader v2.0
├── examples/
│   ├── skill-lock.json              # SEO/GEO lockfile
│   ├── skill-lock-code-review.json  # Code Review lockfile
│   └── skill-lock-finance.json      # Finance lockfile
└── skills/
    │
    │── # Domain: SEO/GEO (Content Optimization)
    ├── seo-knowledge-base/     # Abstract
    ├── geo-optimizer/          # Specialist
    ├── seo-auditor/            # Utility
    ├── content-orchestrator/   # Orchestrator
    │
    │── # Domain: Code Review (Software Development)
    ├── code-standards-base/    # Abstract
    ├── security-auditor/       # Specialist
    ├── performance-optimizer/  # Specialist
    ├── code-review-orchestrator/ # Orchestrator
    │
    │── # Domain: Finance (Investment Analysis)
    ├── financial-rules-base/   # Abstract
    ├── risk-analyzer/          # Specialist
    ├── portfolio-optimizer/    # Specialist
    └── investment-orchestrator/  # Orchestrator
```

## Cross-Domain Pattern

All three domains follow the same architectural pattern — **Orchestrator -> Specialists -> Base**:

| Component | SEO/GEO | Code Review | Finance |
|-----------|---------|-------------|---------|
| Base | `seo-knowledge-base` | `code-standards-base` | `financial-rules-base` |
| Analyzer | `seo-auditor` | `security-auditor` | `risk-analyzer` |
| Optimizer | `geo-optimizer` | `performance-optimizer` | `portfolio-optimizer` |
| Orchestrator | `content-orchestrator` | `code-review-orchestrator` | `investment-orchestrator` |

**Common contracts (polymorphism):**
- `analyze(input) -> Report` — implemented by all analyzers
- `optimize(input) -> OptimizedOutput` — implemented by all optimizers
- `orchestrate(input) -> UnifiedReport` — implemented by all orchestrators

## Key Features

### 1. Progressive Loading

Skills define `[SUMMARY]` (~200 tokens) and `[FULL]` (~2000 tokens) sections:

```markdown
## [SUMMARY]
Essential rules for 80% of cases.

## [FULL]
Complete details when needed.

## [FULL:topic]
Subsection for specific topic.
```

### 2. Dependency Declaration

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

### 3. Abstract Skills with Guards

```markdown
## GUARD
If invoked directly, respond:
"This is an abstract skill. Use geo-optimizer instead."
```

### 4. Lockfiles for Reproducibility

```json
{
  "resolved": {
    "geo-optimizer": {
      "version": "1.0.0",
      "integrity": "sha256:abc123",
      "load_level": "summary"
    }
  },
  "context_budget": {
    "total_tokens": 3847
  }
}
```

### 5. Structured Logging

```
[COMPOSE:START] content-orchestrator@1.0.0
  [DEP:LOADED] seo-knowledge-base@1.2.0 (summary) [200 tokens]
  [DEP:LOADED] geo-optimizer@1.0.0 [850 tokens]
[COMPOSE:COMPLETE] Total: 4250 tokens | Skills: 4
```

## Case Study: Content Engine Degradation

Section 8 of the paper presents a real-world case where a production system of 7 well-built skills suffered **silent degradation** under multi-skill composition. Four of five outputs were fine, but the most instruction-heavy skill (Instagram Carousel) lost critical features — visual annotations, screenshots, production guide — when 5 skills competed for the same context window.

The case proves that **individual skill quality does not guarantee system quality under composition**. The architectural mechanisms proposed in this paper (Progressive Loading, Contract Testing, Context Budget, Structured Logging) directly address this failure mode.

## Read the Paper

The full technical paper is in [PAPER.md](./PAPER.md).

**Topics covered:**
- OOP -> Agent Skills mapping
- SOLID principles for prompts
- Three domain implementations (SEO/GEO, Code Review, Finance)
- Progressive loading spec
- Dependency resolution strategies
- Reproducibility (lockfiles, logging, snapshots, contract testing)
- Circular dependencies and debugging
- Case study: Content Engine degradation
- Lockfile format and logging template

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Ideas welcome:

- [ ] TypeScript/Node.js loader
- [ ] VS Code extension
- [ ] Contract testing framework
- [ ] Skill marketplace prototype
- [ ] Additional domain examples

## References

### Agent Skills & AI Agents
- [Agent Skills Specification](https://agentskills.io)
- [The Complete Guide to Building Skills for Claude](https://docs.anthropic.com) (Anthropic, 2026)
- [Model Context Protocol](https://modelcontextprotocol.io)

### Software Engineering
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Design Patterns (GoF)](https://en.wikipedia.org/wiki/Design_Patterns)

### Security (Code Review Domain)
- [OWASP Top Ten](https://owasp.org/Top10/)
- [CWE Top 25](https://cwe.mitre.org)
- [NIST SSDF](https://csrc.nist.gov)

### Finance (Investment Analysis Domain)
- Markowitz, H. "Portfolio Selection." The Journal of Finance, 1952.
- Sharpe, W. F. "The Sharpe Ratio." The Journal of Portfolio Management, 1994.
- Jorion, P. "Value at Risk." McGraw-Hill, 2006.
- [CFA Institute GIPS](https://www.cfainstitute.org)

## License

MIT - see [LICENSE](./LICENSE)

---

**Author:** [Gustavo Stork](https://github.com/gugastork)
**Published:** March 2026
**Version:** 5.0

*Built on Anthropic's Agent Skills open standard (December 2025) and the official Skills Guide (February 2026)*
