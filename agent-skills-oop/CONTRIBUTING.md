# Contribuindo para Agent Skills OOP

Obrigado por considerar contribuir! Este documento explica como você pode ajudar.

## 🎯 Formas de Contribuir

### 1. Adicionar Novas Skills

O projeto se beneficia de exemplos em diferentes domínios:

- **Coding Skills**: Linting, code review, refactoring
- **Research Skills**: Summarization, fact-checking, citation
- **Business Skills**: Report generation, data analysis
- **Creative Skills**: Writing, editing, translation

### 2. Melhorar Skills Existentes

- Expandir regras e checklist
- Adicionar mais exemplos
- Melhorar documentação

### 3. Melhorar o Loader

- Suporte a TypeScript/Node.js
- Caching de skills
- Validação mais robusta
- Integração com Claude Code / Cursor

### 4. Documentação

- Tradução para outros idiomas
- Tutoriais e guias
- Casos de uso

## 📁 Estrutura de uma Skill

```
skill-name/
├── SKILL.md          # Obrigatório: Instruções procedurais
├── metadata.json     # Obrigatório: Metadados e schemas
└── examples/         # Opcional: Exemplos de uso
    └── example-1.md
```

### SKILL.md

Deve conter:
1. **Frontmatter YAML** com name, version, description, dependencies
2. **Propósito**: O que a skill faz
3. **Instruções**: Como executar
4. **Output**: Formato esperado
5. **Error Handling**: Como lidar com falhas

### metadata.json

Campos obrigatórios:
```json
{
  "name": "skill-name",
  "version": "1.0.0",
  "description": "O que a skill faz"
}
```

Campos recomendados:
```json
{
  "type": "abstract|specialist|utility|orchestrator",
  "dependencies": { "other-skill": "^1.0.0" },
  "triggers": ["quando usar esta skill"],
  "input_schema": { },
  "output_schema": { }
}
```

## 🔧 Convenções

### Versionamento
Use [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: Novas funcionalidades (backward compatible)
- PATCH: Bug fixes

### Tipos de Skill

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `abstract` | Apenas regras/definições | knowledge-base |
| `specialist` | Faz uma transformação específica | optimizer |
| `utility` | Ferramenta auxiliar | auditor, validator |
| `orchestrator` | Coordena outras skills | workflow-manager |

### Dependências

- Skills `abstract` **nunca** devem ter dependências (evita ciclos)
- Use version ranges: `"^1.0.0"` (compatível com 1.x.x)
- Declare **todas** as dependências (mesmo transitivas, se críticas)

## 🧪 Testando

Antes de submeter, verifique:

```bash
# Valida estrutura de todas as skills
python loader.py --validate

# Testa sua skill específica
python loader.py sua-skill --tree
python loader.py sua-skill --compose
```

## 📝 Checklist de PR

- [ ] Skill tem SKILL.md e metadata.json
- [ ] Versão semântica definida
- [ ] Dependências declaradas corretamente
- [ ] Loader valida sem erros
- [ ] README atualizado se necessário

## 💬 Dúvidas?

Abra uma issue! Toda pergunta é bem-vinda.

---

Feito com ❤️ pela comunidade Agent Skills
