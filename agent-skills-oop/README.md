# Agent Skills OOP

> Applying Object-Oriented Programming principles to the Agent Skills open standard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Open%20Standard-blue)](https://agentskills.io)
[![Version](https://img.shields.io/badge/version-4.0-green)](./PAPER.md)

## 🎯 The Problem

As AI agents grow more capable, their prompts become **monolithic nightmares**:
- 10k+ tokens always loaded
- Rules copy-pasted across Skills
- No dependency management
- Impossible to test in isolation

## 💡 The Solution

Treat Skills as **composable objects** with OOP principles:

| Principle | Application |
|-----------|-------------|
| **Encapsulation** | Each Skill isolates its knowledge |
| **Composition** | Skills load other Skills dynamically |
| **Abstraction** | Base Skills define contracts |
| **SOLID** | All 5 principles apply to Skill design |

```
┌─────────────────────────────────────────────┐
│          content-orchestrator               │
│              (Orchestrator)                 │
└───────┬─────────────┬─────────────┬─────────┘
        │             │             │
        ▼             ▼             ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│seo-auditor│ │geo-optim. │ │  writer   │
│ (Utility) │ │(Specialist)│ │(Generator)│
└─────┬─────┘ └─────┬─────┘ └─────┬─────┘
      │             │             │
      └──────┬──────┴──────┬──────┘
             │             │
             ▼             ▼
    ┌─────────────────────────────┐
    │    seo-knowledge-base       │
    │       (Abstract)            │
    │  [SUMMARY] → 200 tokens     │
    │  [FULL] → 1500 tokens       │
    └─────────────────────────────┘
```

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/gustavostork/agent-skills-oop.git
cd agent-skills-oop

# List available skills
python loader.py --list

# View dependency tree
python loader.py content-orchestrator --tree

# Generate lockfile for reproducibility
python loader.py content-orchestrator --lockfile

# Compose full context
python loader.py content-orchestrator --compose --output context.md
```

## 📁 Repository Structure

```
agent-skills-oop/
├── README.md              # This file
├── PAPER.md               # Full technical paper (v4.0)
├── MARKETING.md           # LinkedIn/Twitter posts
├── CONTRIBUTING.md        # Contribution guidelines
├── LICENSE                # MIT
├── loader.py              # Python loader v2.0
├── examples/
│   └── skill-lock.json    # Example lockfile
└── skills/
    ├── seo-knowledge-base/   # 📚 Abstract (rules only)
    │   ├── SKILL.md          #    with [SUMMARY]/[FULL]
    │   └── metadata.json
    ├── geo-optimizer/        # 🔧 Specialist
    ├── seo-auditor/          # 🔍 Utility
    └── content-orchestrator/ # 🎯 Orchestrator
```

## ✨ Key Features

### 1. Progressive Loading

Skills define `[SUMMARY]` (~200 tokens) and `[FULL]` (~2000 tokens) sections:

```markdown
## [SUMMARY]
Essential rules for 80% of cases.

## [FULL]
Complete details when needed.

## [FULL:geo]
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
"⚠️ This is an abstract skill. Use geo-optimizer instead."
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
  "total_tokens": 3847
}
```

### 5. Structured Logging

```
[COMPOSE:START] content-orchestrator@1.0.0
  [DEP:LOADED] seo-knowledge-base@1.2.0 (summary) [200 tokens]
  [DEP:LOADED] geo-optimizer@1.0.0 [850 tokens]
[COMPOSE:COMPLETE] Total: 4250 tokens | Skills: 4
```

## 📖 Read the Paper

The full technical paper is in [PAPER.md](./PAPER.md).

**Topics covered:**
- OOP → Agent Skills mapping
- SOLID principles for prompts
- Progressive loading spec
- Dependency resolution strategies
- Lockfile format
- Limitations and mitigations

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Ideas welcome:

- [ ] More domain examples (coding, research, etc.)
- [ ] TypeScript/Node.js loader
- [ ] VS Code extension
- [ ] Contract testing framework
- [ ] Skill marketplace prototype

## 📚 References

- [Agent Skills Specification](https://agentskills.io)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Design Patterns (GoF)](https://en.wikipedia.org/wiki/Design_Patterns)

## 📄 License

MIT - see [LICENSE](./LICENSE)

---

**Author:** [Gustavo Stork](https://github.com/gustavostork)  
**Published:** December 20, 2025  
**Version:** 4.0

*Created in response to Anthropic's Agent Skills open standard announcement (December 18, 2025)*
