#!/usr/bin/env python3
"""
Agent Skills Loader v2.0 - OOP-style Dependency Resolution with Progressive Loading

Este loader implementa:
- Resolução de dependências para Agent Skills
- Suporte a load levels (summary/full/full:section)
- Geração de lockfiles para reprodutibilidade
- Logging estruturado de composição

Uso:
    python loader.py <skill-name>              # Carrega skill com dependências
    python loader.py <skill-name> --tree       # Mostra árvore de dependências
    python loader.py <skill-name> --compose    # Compõe contexto completo
    python loader.py <skill-name> --lockfile   # Gera lockfile
    python loader.py --list                    # Lista skills disponíveis
    python loader.py --validate                # Valida todas as skills

Author: Gustavo Stork
Version: 2.0.0
Date: 2025-12-20
"""

import os
import re
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("⚠️  PyYAML não instalado. Frontmatter YAML será ignorado.")


@dataclass
class Skill:
    """Representa uma Agent Skill carregada"""
    name: str
    version: str
    description: str
    path: Path
    content: str
    metadata: Dict
    dependencies: Dict = field(default_factory=dict)
    skill_type: str = "unknown"
    sections: Dict[str, str] = field(default_factory=dict)
    
    def __repr__(self):
        return f"Skill({self.name}@{self.version})"
    
    def get_integrity(self) -> str:
        """Gera hash SHA256 do conteúdo para verificação"""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]
    
    def estimate_tokens(self, section: str = "full") -> int:
        """Estima tokens baseado no conteúdo (~4 chars/token)"""
        content = self.get_section(section)
        return len(content) // 4
    
    def get_section(self, section: str = "full") -> str:
        """Retorna seção específica do conteúdo"""
        if section == "full":
            return self.content
        elif section == "summary":
            return self.sections.get("summary", self.content)
        elif section.startswith("full:"):
            subsection = section.replace("full:", "")
            return self.sections.get(f"full:{subsection}", self.content)
        return self.content


class SkillLoader:
    """
    Loader de Agent Skills v2.0 com Progressive Loading.
    
    Features:
    - Resolução de dependências com detecção de ciclos
    - Suporte a load levels (summary/full/full:section)
    - Geração de lockfiles
    - Logging estruturado
    """
    
    def __init__(self, skills_dir: str = "./skills", verbose: bool = False):
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, Skill] = {}
        self.loading_stack: Set[str] = set()
        self.verbose = verbose
        self.composition_log: List[str] = []
        
    def log(self, message: str):
        """Adiciona mensagem ao log de composição"""
        self.composition_log.append(message)
        if self.verbose:
            print(message)
    
    def discover_skills(self) -> List[str]:
        """Lista todas as skills disponíveis"""
        skills = []
        if not self.skills_dir.exists():
            return skills
            
        for item in self.skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                skill_file = item / "SKILL.md"
                meta_file = item / "metadata.json"
                if skill_file.exists() or meta_file.exists():
                    skills.append(item.name)
        return sorted(skills)
    
    def load_metadata(self, skill_path: Path) -> Dict:
        """Carrega metadata.json"""
        meta_file = skill_path / "metadata.json"
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def load_skill_content(self, skill_path: Path) -> str:
        """Carrega conteúdo do SKILL.md"""
        skill_file = skill_path / "SKILL.md"
        if skill_file.exists():
            with open(skill_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Extrai YAML frontmatter"""
        if not content.startswith('---'):
            return {}, content
            
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
            
        if HAS_YAML:
            try:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter or {}, parts[2].strip()
            except yaml.YAMLError:
                return {}, content
        return {}, parts[2].strip()
    
    def parse_sections(self, content: str) -> Dict[str, str]:
        """Extrai seções [SUMMARY] e [FULL] do conteúdo"""
        sections = {}
        
        # Procura por [SUMMARY]
        summary_match = re.search(
            r'##\s*\[SUMMARY\](.*?)(?=##\s*\[FULL|$)', 
            content, 
            re.DOTALL | re.IGNORECASE
        )
        if summary_match:
            sections['summary'] = summary_match.group(1).strip()
        
        # Procura por [FULL] e subseções [FULL:xxx]
        full_matches = re.finditer(
            r'##\s*\[FULL(?::(\w+))?\](.*?)(?=##\s*\[FULL|##\s*\[ABSTRACT|$)', 
            content, 
            re.DOTALL | re.IGNORECASE
        )
        for match in full_matches:
            subsection = match.group(1)
            if subsection:
                sections[f'full:{subsection}'] = match.group(2).strip()
            else:
                sections['full'] = match.group(2).strip()
        
        return sections
    
    def load_skill(self, name: str, resolve_deps: bool = True) -> Skill:
        """Carrega uma skill pelo nome"""
        if name in self.loaded_skills:
            return self.loaded_skills[name]
        
        if name in self.loading_stack:
            cycle = " -> ".join(self.loading_stack) + f" -> {name}"
            raise ValueError(f"🔄 Dependência circular detectada: {cycle}")
        
        skill_path = self.skills_dir / name
        if not skill_path.exists():
            raise ValueError(f"❌ Skill não encontrada: {name}")
        
        self.loading_stack.add(name)
        
        try:
            metadata = self.load_metadata(skill_path)
            content = self.load_skill_content(skill_path)
            frontmatter, body = self.parse_frontmatter(content)
            sections = self.parse_sections(content)
            
            merged_meta = {**frontmatter, **metadata}
            
            # Parse dependencies (suporta formato antigo e novo)
            raw_deps = merged_meta.get('dependencies', {})
            dependencies = {}
            if isinstance(raw_deps, dict):
                for dep_name, dep_info in raw_deps.items():
                    if isinstance(dep_info, dict):
                        dependencies[dep_name] = dep_info
                    else:
                        dependencies[dep_name] = {"version": dep_info, "load": "full"}
            elif isinstance(raw_deps, list):
                for dep in raw_deps:
                    if isinstance(dep, dict):
                        dependencies[dep['name']] = dep
                    else:
                        dependencies[dep] = {"version": "*", "load": "full"}
            
            skill = Skill(
                name=name,
                version=merged_meta.get('version', '0.0.0'),
                description=merged_meta.get('description', ''),
                path=skill_path,
                content=content,
                metadata=merged_meta,
                dependencies=dependencies,
                skill_type=merged_meta.get('type', 'unknown'),
                sections=sections
            )
            
            if resolve_deps and dependencies:
                for dep_name in dependencies:
                    if dep_name not in self.loaded_skills:
                        self.load_skill(dep_name, resolve_deps=True)
            
            self.loaded_skills[name] = skill
            return skill
            
        finally:
            self.loading_stack.discard(name)
    
    def get_dependency_tree(self, name: str, indent: int = 0) -> str:
        """Gera árvore visual de dependências"""
        try:
            skill = self.load_skill(name, resolve_deps=False)
        except ValueError:
            return f"{'  ' * indent}❌ {name} (não encontrada)"
        
        prefix = "  " * indent
        icon = self._get_type_icon(skill.skill_type)
        
        deps_info = skill.dependencies
        load_levels = []
        for dep_name, dep_info in deps_info.items():
            load = dep_info.get('load', 'full') if isinstance(dep_info, dict) else 'full'
            load_levels.append(f"{dep_name}({load})")
        
        lines = [f"{prefix}{icon} {skill.name}@{skill.version}"]
        
        for dep_name, dep_info in deps_info.items():
            load = dep_info.get('load', 'full') if isinstance(dep_info, dict) else 'full'
            lines.append(self.get_dependency_tree(dep_name, indent + 1))
            # Adiciona indicador de load level
            if indent == 0:
                lines[-1] = lines[-1].replace('\n', f' [{load}]\n', 1)
        
        return "\n".join(lines)
    
    def _get_type_icon(self, skill_type: str) -> str:
        """Retorna ícone baseado no tipo"""
        icons = {
            "abstract": "📚",
            "specialist": "🔧",
            "utility": "🔍",
            "orchestrator": "🎯",
            "unknown": "📄"
        }
        return icons.get(skill_type, "📄")
    
    def compose_context(self, name: str, with_logging: bool = True) -> str:
        """Compõe contexto completo com dependências"""
        self.composition_log = []
        skill = self.load_skill(name)
        
        if with_logging:
            self.log(f"[COMPOSE:START] {name}@{skill.version}")
        
        resolved = self._topological_sort(name)
        sections = []
        total_tokens = 0
        
        # Adiciona dependências
        for dep_name in resolved[:-1]:
            dep_skill = self.loaded_skills[dep_name]
            
            # Determina load level
            parent_deps = skill.dependencies
            load_level = "full"
            for pname, pinfo in parent_deps.items():
                if pname == dep_name and isinstance(pinfo, dict):
                    load_level = pinfo.get('load', 'full')
            
            content = dep_skill.get_section(load_level)
            tokens = len(content) // 4
            total_tokens += tokens
            
            if with_logging:
                self.log(f"  [DEP:LOADED] {dep_name}@{dep_skill.version} ({load_level}) [{tokens} tokens]")
            
            sections.append(f"<!-- DEPENDENCY: {dep_name}@{dep_skill.version} ({load_level}) -->")
            sections.append(content)
            sections.append(f"<!-- END: {dep_name} -->\n")
        
        # Adiciona skill principal
        main_tokens = skill.estimate_tokens()
        total_tokens += main_tokens
        
        sections.append(f"<!-- MAIN: {name}@{skill.version} -->")
        sections.append(skill.content)
        
        if with_logging:
            self.log(f"[COMPOSE:LOADED] {name}@{skill.version} [{main_tokens} tokens]")
            self.log(f"[COMPOSE:COMPLETE] Total: {total_tokens} tokens | Skills: {len(resolved)}")
        
        return "\n".join(sections)
    
    def _topological_sort(self, name: str) -> List[str]:
        """Ordena dependências topologicamente"""
        visited = set()
        result = []
        
        def visit(n: str):
            if n in visited:
                return
            visited.add(n)
            
            if n in self.loaded_skills:
                skill = self.loaded_skills[n]
                for dep in skill.dependencies:
                    visit(dep)
            
            result.append(n)
        
        visit(name)
        return result
    
    def generate_lockfile(self, name: str) -> Dict:
        """Gera lockfile para reprodutibilidade"""
        skill = self.load_skill(name)
        resolved = self._topological_sort(name)
        
        lockfile = {
            "$schema": "https://agentskills.io/schemas/lockfile-v1.json",
            "generated": datetime.now(timezone.utc).isoformat(),
            "generator": "skill-loader@2.0.0",
            "root": name,
            "resolved": {},
            "context_budget": {
                "total_tokens": 0,
                "by_skill": {}
            },
            "composition_order": resolved
        }
        
        for skill_name in resolved:
            s = self.loaded_skills[skill_name]
            
            # Determina load level
            load_level = "full"
            if skill_name != name:
                parent = self.loaded_skills[name]
                for pname, pinfo in parent.dependencies.items():
                    if pname == skill_name and isinstance(pinfo, dict):
                        load_level = pinfo.get('load', 'full')
            
            tokens = s.estimate_tokens(load_level)
            
            lockfile["resolved"][skill_name] = {
                "version": s.version,
                "path": str(s.path),
                "integrity": f"sha256:{s.get_integrity()}",
                "dependencies": list(s.dependencies.keys()),
                "load_level": load_level,
                "type": s.skill_type
            }
            
            lockfile["context_budget"]["by_skill"][f"{skill_name}:{load_level}"] = tokens
            lockfile["context_budget"]["total_tokens"] += tokens
        
        return lockfile
    
    def validate_all(self) -> Dict[str, List[str]]:
        """Valida todas as skills"""
        issues = {}
        
        for skill_name in self.discover_skills():
            skill_issues = []
            skill_path = self.skills_dir / skill_name
            
            if not (skill_path / "SKILL.md").exists():
                skill_issues.append("SKILL.md ausente")
            
            if not (skill_path / "metadata.json").exists():
                skill_issues.append("metadata.json ausente")
            else:
                try:
                    meta = self.load_metadata(skill_path)
                    if 'name' not in meta:
                        skill_issues.append("metadata: 'name' ausente")
                    if 'version' not in meta:
                        skill_issues.append("metadata: 'version' ausente")
                    if 'description' not in meta:
                        skill_issues.append("metadata: 'description' ausente")
                except json.JSONDecodeError as e:
                    skill_issues.append(f"metadata.json inválido: {e}")
            
            try:
                skill = self.load_skill(skill_name)
                for dep in skill.dependencies:
                    dep_path = self.skills_dir / dep
                    if not dep_path.exists():
                        skill_issues.append(f"dependência não encontrada: {dep}")
            except ValueError as e:
                skill_issues.append(str(e))
            
            if skill_issues:
                issues[skill_name] = skill_issues
        
        return issues


def main():
    """CLI principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Agent Skills Loader v2.0 - OOP Dependencies + Progressive Loading"
    )
    parser.add_argument("skill", nargs="?", help="Nome da skill")
    parser.add_argument("--list", "-l", action="store_true", help="Lista skills")
    parser.add_argument("--tree", "-t", action="store_true", help="Árvore de dependências")
    parser.add_argument("--compose", "-c", action="store_true", help="Compõe contexto")
    parser.add_argument("--lockfile", action="store_true", help="Gera lockfile")
    parser.add_argument("--validate", "-v", action="store_true", help="Valida skills")
    parser.add_argument("--dir", "-d", default="./skills", help="Diretório das skills")
    parser.add_argument("--output", "-o", help="Arquivo de saída")
    parser.add_argument("--verbose", action="store_true", help="Logs detalhados")
    
    args = parser.parse_args()
    loader = SkillLoader(args.dir, verbose=args.verbose)
    
    if args.list:
        print("\n📦 Skills disponíveis:\n")
        for name in loader.discover_skills():
            try:
                skill = loader.load_skill(name, resolve_deps=False)
                icon = loader._get_type_icon(skill.skill_type)
                deps = len(skill.dependencies)
                tokens = skill.estimate_tokens('summary')
                print(f"  {icon} {name}@{skill.version} ({deps} deps, ~{tokens} tokens)")
                print(f"     {skill.description[:55]}...")
            except Exception as e:
                print(f"  ❌ {name} - Erro: {e}")
        print()
        return
    
    if args.validate:
        print("\n🔍 Validando skills...\n")
        issues = loader.validate_all()
        if not issues:
            print("✅ Todas as skills são válidas!")
        else:
            for skill_name, skill_issues in issues.items():
                print(f"❌ {skill_name}:")
                for issue in skill_issues:
                    print(f"   - {issue}")
        print()
        return
    
    if not args.skill:
        parser.print_help()
        return
    
    if args.tree:
        print(f"\n🌳 Árvore de dependências: {args.skill}\n")
        print(loader.get_dependency_tree(args.skill))
        print()
        return
    
    if args.lockfile:
        try:
            lockfile = loader.generate_lockfile(args.skill)
            output = json.dumps(lockfile, indent=2)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"✅ Lockfile salvo em: {args.output}")
            else:
                print(output)
        except ValueError as e:
            print(f"❌ Erro: {e}")
        return
    
    if args.compose:
        try:
            context = loader.compose_context(args.skill)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(context)
                print(f"✅ Contexto salvo em: {args.output}")
                print("\n📋 Log de composição:")
                for log in loader.composition_log:
                    print(f"  {log}")
            else:
                print(context)
        except ValueError as e:
            print(f"❌ Erro: {e}")
        return
    
    # Default: mostra info da skill
    try:
        skill = loader.load_skill(args.skill)
        print(f"\n📄 {skill.name}@{skill.version}")
        print(f"   Tipo: {skill.skill_type}")
        print(f"   Descrição: {skill.description}")
        print(f"   Tokens (full): ~{skill.estimate_tokens('full')}")
        if skill.sections.get('summary'):
            print(f"   Tokens (summary): ~{skill.estimate_tokens('summary')}")
        print(f"   Dependências: {list(skill.dependencies.keys()) or 'Nenhuma'}")
        print(f"   Path: {skill.path}")
        
        if skill.dependencies:
            print("\n🌳 Árvore:")
            print(loader.get_dependency_tree(args.skill))
        print()
        
    except ValueError as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()
