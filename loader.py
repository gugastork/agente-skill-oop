#!/usr/bin/env python3
"""
Agent Skills Loader v3.0 - OOP-style Dependency Resolution with Progressive Loading

Este loader implementa:
- Resolução de dependências para Agent Skills
- Suporte a load levels (summary/full/full:section)
- Geração de lockfiles para reprodutibilidade
- Logging estruturado de composição
- Demo mode: execução demonstrativa sem dependências externas
- Run mode: execução real via Claude API (requer anthropic SDK)
- Clean compose: gera system prompt pronto para uso

Uso:
    python loader.py <skill-name>              # Carrega skill com dependências
    python loader.py <skill-name> --tree       # Mostra árvore de dependências
    python loader.py <skill-name> --compose    # Compõe contexto completo
    python loader.py <skill-name> --compose --clean  # Gera system prompt limpo
    python loader.py <skill-name> --lockfile   # Gera lockfile
    python loader.py <skill-name> --demo       # Executa demonstração com dados de exemplo
    python loader.py <skill-name> --run --input file  # Executa via Claude API
    python loader.py --list                    # Lista skills disponíveis
    python loader.py --validate                # Valida todas as skills

Author: Gustavo Stork
Version: 3.0.0
Date: 2025-12-20
"""

import os
import re
import json
import sys
import hashlib
import time
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
            "generator": "skill-loader@3.0.0",
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


class DemoRunner:
    """
    Runs self-contained demonstrations of orchestrator skills.
    Uses real SkillLoader.compose_context() for dependency resolution,
    then simulates specialist processing with sample data.
    """

    SAMPLES_DIR = Path(__file__).parent / "examples" / "samples"

    def __init__(self, loader: SkillLoader):
        self.loader = loader

    def _print_phase(self, phase: str, message: str):
        print(f"  [{phase}] {message}")

    def _print_progress(self, label: str, steps: List[str], delay: float = 0.3):
        for step in steps:
            time.sleep(delay)
            print(f"    -> {label}: {step}")

    def run(self, skill_name: str):
        demos = {
            "code-review-orchestrator": self._demo_code_review,
            "content-orchestrator": self._demo_content,
            "investment-orchestrator": self._demo_investment,
        }
        if skill_name not in demos:
            print(f"\n❌ No demo available for '{skill_name}'.")
            print(f"   Available demos: {', '.join(demos.keys())}")
            return
        demos[skill_name]()

    def _compose_and_show_log(self, skill_name: str):
        print(f"\n{'='*70}")
        print(f"  DEMO: {skill_name}")
        print(f"  Mode: Demonstration with sample data")
        print(f"{'='*70}\n")

        print("Phase 0: Composing context (real dependency resolution)\n")
        context = self.loader.compose_context(skill_name)
        for log_line in self.loader.composition_log:
            print(f"  {log_line}")
        print()
        return context

    # ── Code Review Demo ──────────────────────────────────────────────

    def _demo_code_review(self):
        self._compose_and_show_log("code-review-orchestrator")

        sample_path = self.SAMPLES_DIR / "vulnerable_app.py"
        if sample_path.exists():
            with open(sample_path, "r") as f:
                lines = f.readlines()
            print(f"Phase 1: Receiving code\n")
            self._print_phase("PHASE:RECEIVE", f"Code: {len(lines)} lines | Language: Python")
            print(f"  Source: {sample_path}\n")
        else:
            lines = []
            self._print_phase("PHASE:RECEIVE", "Code: 90 lines | Language: Python (built-in sample)")
            print()

        # Phase 2: Security Audit
        print("Phase 2: Security Audit (security-auditor)\n")
        security_findings = [
            {"id": "SEC-001", "severity": "Critical", "type": "SQL Injection (CWE-89)",
             "location": "vulnerable_app.py:31", "description": "Direct string formatting in SQL query allows injection via 'username' parameter"},
            {"id": "SEC-002", "severity": "Critical", "type": "XSS (CWE-79)",
             "location": "vulnerable_app.py:39", "description": "User input rendered directly in HTML template via render_template_string"},
            {"id": "SEC-003", "severity": "Critical", "type": "Insecure Deserialization (CWE-502)",
             "location": "vulnerable_app.py:46", "description": "pickle.loads() on untrusted POST data enables remote code execution"},
            {"id": "SEC-004", "severity": "High", "type": "Weak Hashing (CWE-328)",
             "location": "vulnerable_app.py:52", "description": "MD5 used for password hashing — no salt, trivially crackable"},
            {"id": "SEC-005", "severity": "High", "type": "Path Traversal (CWE-22)",
             "location": "vulnerable_app.py:58", "description": "No sanitization of file path allows reading arbitrary files"},
            {"id": "SEC-006", "severity": "Medium", "type": "Hardcoded Credentials (CWE-798)",
             "location": "vulnerable_app.py:14-16", "description": "DB_PASSWORD, SECRET_KEY, and API_TOKEN hardcoded in source"},
            {"id": "SEC-007", "severity": "Medium", "type": "Debug Mode in Production",
             "location": "vulnerable_app.py:93", "description": "Flask debug=True exposes debugger and stack traces"},
        ]
        self._print_progress("Scanning", [
            "Checking for injection vulnerabilities...",
            "Analyzing authentication and crypto...",
            "Checking input validation and file handling...",
            "Reviewing configuration and secrets...",
        ])
        for f in security_findings:
            print(f"    [{f['severity'].upper():>8}] {f['type']} at {f['location']}")
        self._print_phase("PHASE:SECURITY", f"Vulnerabilities: {len(security_findings)} | Risk: Critical")
        print()

        # Phase 3: Performance Check
        print("Phase 3: Performance Check (performance-optimizer)\n")
        perf_findings = [
            {"id": "PERF-001", "severity": "High", "type": "N+1 Query Pattern",
             "location": "vulnerable_app.py:65-72", "suggestion": "Use JOIN query: SELECT o.*, oi.* FROM orders o JOIN order_items oi ON o.id = oi.order_id"},
            {"id": "PERF-002", "severity": "High", "type": "Unbounded Query",
             "location": "vulnerable_app.py:78", "suggestion": "Add LIMIT/OFFSET pagination: SELECT * FROM logs ORDER BY created_at DESC LIMIT 100 OFFSET 0"},
            {"id": "PERF-003", "severity": "Medium", "type": "Synchronous Blocking",
             "location": "vulnerable_app.py:85", "suggestion": "Move to background task (Celery/RQ) or use async handler"},
        ]
        self._print_progress("Profiling", [
            "Analyzing database query patterns...",
            "Checking for blocking operations...",
            "Evaluating resource usage...",
        ])
        for f in perf_findings:
            print(f"    [{f['severity'].upper():>8}] {f['type']} at {f['location']}")
            print(f"              Fix: {f['suggestion'][:80]}")
        self._print_phase("PHASE:PERFORMANCE", f"Optimizations: {len(perf_findings)} | Score: 45/100")
        print()

        # Phase 4: Unified Report
        print("Phase 4: Generating Unified Report\n")
        security_score = 25
        performance_score = 45
        solid_score = 60
        overall = int(security_score * 0.50 + performance_score * 0.30 + solid_score * 0.20)
        grade = "F" if overall < 60 else "D" if overall < 70 else "C" if overall < 80 else "B" if overall < 90 else "A"

        report = {
            "review_report": {
                "overall_score": overall,
                "grade": grade,
                "summary": f"Code has {len(security_findings)} security vulnerabilities (3 critical) and {len(perf_findings)} performance issues.",
                "security": {
                    "score": security_score,
                    "findings": security_findings,
                },
                "performance": {
                    "score": performance_score,
                    "optimizations": perf_findings,
                },
                "solid_compliance": {
                    "score": solid_score,
                    "issues": [
                        "No separation between route handlers and business logic (SRP violation)",
                        "Database connection not abstracted (DIP violation)",
                    ],
                },
                "priority_actions": [
                    {"priority": 1, "type": "security", "severity": "Critical",
                     "description": "Fix SQL Injection in vulnerable_app.py:31 — use parameterized queries"},
                    {"priority": 2, "type": "security", "severity": "Critical",
                     "description": "Fix XSS in vulnerable_app.py:39 — use Jinja2 auto-escaping"},
                    {"priority": 3, "type": "security", "severity": "Critical",
                     "description": "Remove pickle.loads() in vulnerable_app.py:46 — use JSON deserialization"},
                    {"priority": 4, "type": "security", "severity": "High",
                     "description": "Replace MD5 with bcrypt/argon2 in vulnerable_app.py:52"},
                    {"priority": 5, "type": "performance", "severity": "High",
                     "description": "Fix N+1 queries in vulnerable_app.py:65 — use SQL JOIN"},
                ],
                "composition_log": "\n".join(self.loader.composition_log),
            }
        }

        self._print_phase("PHASE:REPORT", f"Final Score: {overall}/100 | Grade: {grade}")
        print()
        print("Output (JSON):\n")
        print(json.dumps(report, indent=2))
        print(f"\n{'='*70}")
        print(f"  Demo complete. This was a demonstration with sample data.")
        print(f"  The dependency resolution and composition logs above are real.")
        print(f"{'='*70}\n")

    # ── Content Orchestrator Demo ─────────────────────────────────────

    def _demo_content(self):
        self._compose_and_show_log("content-orchestrator")

        sample_path = self.SAMPLES_DIR / "article_draft.txt"
        if sample_path.exists():
            with open(sample_path, "r") as f:
                content = f.read()
            word_count = len(content.split())
            print(f"Phase 1: Receiving draft\n")
            self._print_phase("PHASE:DRAFT", f"Source: {sample_path}")
            self._print_phase("PHASE:DRAFT", f"Words: {word_count} | Topic: AI in Healthcare")
            print()
        else:
            word_count = 350
            self._print_phase("PHASE:DRAFT", "Words: 350 | Topic: AI in Healthcare (built-in sample)")
            print()

        # Phase 2: Audit
        print("Phase 2: SEO/GEO Audit (seo-auditor)\n")
        self._print_progress("Auditing", [
            "Checking title tag and meta description...",
            "Analyzing keyword density and placement...",
            "Evaluating heading structure (H1/H2/H3)...",
            "Checking content depth and E-E-A-T signals...",
            "Analyzing GEO optimization signals...",
        ])
        audit_issues = [
            "Title too generic — no target keyword in H1",
            "No meta description provided",
            "Thin content: paragraphs lack depth, data, or citations",
            "Keyword stuffing: 'AI in healthcare' repeated 12 times with no variation",
            "No internal/external links",
            "Missing schema markup signals",
            "No author expertise signals (E-E-A-T)",
            "Weak conclusion — no clear CTA",
        ]
        for issue in audit_issues:
            print(f"    [ISSUE] {issue}")
        initial_score = 32
        self._print_phase("PHASE:AUDIT", f"Score: {initial_score}/100 (Grade: F) | Issues: {len(audit_issues)}")
        print()

        # Phase 3: Optimization
        print("Phase 3: GEO Optimization (geo-optimizer)\n")
        self._print_progress("Optimizing", [
            "Rewriting H1 with primary keyword...",
            "Adding statistical citations and data points...",
            "Restructuring for featured snippet eligibility...",
            "Adding semantic variations and LSI keywords...",
            "Inserting authoritative source citations...",
            "Adding structured FAQ section...",
            "Optimizing for AI overview inclusion...",
        ], delay=0.25)
        self._print_phase("PHASE:OPTIMIZE", "Level: aggressive | Changes: 12 applied")
        print()

        # Phase 4: Validation
        print("Phase 4: Final Validation (seo-auditor)\n")
        final_score = 84
        self._print_phase("PHASE:VALIDATE", f"Score: {final_score}/100 (Grade: B) | Improvement: +{final_score - initial_score} points")
        print()

        # Phase 5: Delivery
        print("Phase 5: Generating Output\n")
        report = {
            "final_content": "[Optimized article content — 1,850 words with citations, data, and structured headings]",
            "metadata": {
                "word_count": 1850,
                "reading_time": "7 min",
                "target_keywords": [
                    "AI in healthcare",
                    "artificial intelligence medical diagnosis",
                    "healthcare AI applications 2026",
                    "machine learning patient outcomes",
                ],
            },
            "audit_summary": {
                "initial_score": initial_score,
                "final_score": final_score,
                "improvement": f"+{final_score - initial_score} points",
                "iterations": 2,
            },
            "seo_checklist": {
                "meta_title": "AI in Healthcare: How Machine Learning Is Transforming Medical Diagnosis in 2026",
                "meta_description": "Discover how AI is revolutionizing healthcare with 40% faster diagnoses and $150B in projected savings. Data-backed guide for healthcare leaders.",
                "suggested_slug": "ai-healthcare-medical-diagnosis-2026",
            },
            "composition_log": "\n".join(self.loader.composition_log),
        }
        self._print_phase("PHASE:DELIVER", "Complete | Iterations: 2")
        print()
        print("Output (JSON):\n")
        print(json.dumps(report, indent=2))
        print(f"\n{'='*70}")
        print(f"  Demo complete. This was a demonstration with sample data.")
        print(f"  The dependency resolution and composition logs above are real.")
        print(f"{'='*70}\n")

    # ── Investment Orchestrator Demo ──────────────────────────────────

    def _demo_investment(self):
        self._compose_and_show_log("investment-orchestrator")

        sample_path = self.SAMPLES_DIR / "portfolio.json"
        portfolio_data = None
        if sample_path.exists():
            with open(sample_path, "r") as f:
                portfolio_data = json.load(f)

        if portfolio_data:
            p = portfolio_data["portfolio"]
            assets = p["assets"]
            print(f"Phase 1: Receiving portfolio\n")
            self._print_phase("PHASE:RECEIVE", f"Portfolio: {len(assets)} assets | Value: ${p['total_value']:,.0f}")
            self._print_phase("PHASE:RECEIVE", f"Risk tolerance: {p['risk_tolerance']} | Horizon: {p['investment_horizon']}")
            print(f"  Source: {sample_path}\n")
            print(f"  Current allocation:")
            for a in assets:
                print(f"    {a['symbol']:>6} {a['allocation_pct']:5.1f}%  ${a['value']:>10,.0f}  ({a['sector']})")
            print()
        else:
            print("Phase 1: Receiving portfolio (built-in sample)\n")
            self._print_phase("PHASE:RECEIVE", "Portfolio: 6 assets | Value: $500,000")
            print()

        # Phase 2: Risk Analysis
        print("Phase 2: Risk Analysis (risk-analyzer)\n")
        self._print_progress("Analyzing", [
            "Calculating portfolio VaR (95% confidence)...",
            "Computing Sharpe and Sortino ratios...",
            "Evaluating sector concentration risk...",
            "Checking single-stock exposure limits...",
            "Assessing correlation matrix...",
        ])
        risk_findings = [
            {"severity": "Critical", "finding": "Technology sector at 90% — exceeds 40% maximum for moderate risk profile"},
            {"severity": "Critical", "finding": "AAPL at 35% — single-stock exposure exceeds 10% recommended limit"},
            {"severity": "High", "finding": "Fixed income at 5% — well below 20-40% range for moderate profile"},
            {"severity": "High", "finding": "No international diversification — 100% US equity exposure"},
            {"severity": "Medium", "finding": "Portfolio beta of 1.35 indicates higher systematic risk than benchmark"},
        ]
        for f in risk_findings:
            print(f"    [{f['severity'].upper():>8}] {f['finding']}")
        self._print_phase("PHASE:RISK", "Level: High | VaR(95%): 12.3% | Sharpe: 0.62")
        print()

        # Phase 3: Portfolio Optimization
        print("Phase 3: Portfolio Optimization (portfolio-optimizer)\n")
        self._print_progress("Optimizing", [
            "Running mean-variance optimization (Markowitz)...",
            "Applying risk tolerance constraints...",
            "Calculating efficient frontier position...",
            "Generating rebalancing recommendations...",
        ])
        suggested = [
            {"symbol": "AAPL", "current": 35.0, "suggested": 12.0, "action": "SELL"},
            {"symbol": "MSFT", "current": 25.0, "suggested": 10.0, "action": "SELL"},
            {"symbol": "GOOGL", "current": 20.0, "suggested": 8.0, "action": "SELL"},
            {"symbol": "AMZN", "current": 10.0, "suggested": 5.0, "action": "SELL"},
            {"symbol": "BND", "current": 5.0, "suggested": 25.0, "action": "BUY"},
            {"symbol": "VNQ", "current": 5.0, "suggested": 10.0, "action": "BUY"},
            {"symbol": "VXUS", "current": 0.0, "suggested": 15.0, "action": "BUY"},
            {"symbol": "GLD", "current": 0.0, "suggested": 8.0, "action": "BUY"},
            {"symbol": "TIP", "current": 0.0, "suggested": 7.0, "action": "BUY"},
        ]
        print(f"\n  Suggested rebalancing:")
        print(f"    {'Symbol':>6} {'Current':>8} {'Target':>8} {'Action':>6}")
        print(f"    {'------':>6} {'-------':>8} {'------':>8} {'------':>6}")
        for s in suggested:
            print(f"    {s['symbol']:>6} {s['current']:>7.1f}% {s['suggested']:>7.1f}% {s['action']:>6}")
        self._print_phase("PHASE:OPTIMIZE", "Sharpe: 0.62 -> 1.18 | Changes: 9")
        print()

        # Phase 4: Action Plan
        print("Phase 4: Generating Action Plan\n")
        report = {
            "investment_report": {
                "overall_assessment": "High Risk — Aggressive Rebalancing Recommended",
                "risk_analysis": {
                    "risk_level": "High",
                    "var_95": 0.123,
                    "sharpe": 0.62,
                    "sortino": 0.71,
                    "beta": 1.35,
                    "concentration_risk": "Critical — 90% in Technology",
                },
                "optimization": {
                    "current_sharpe": 0.62,
                    "optimized_sharpe": 1.18,
                    "improvement_pct": 90.3,
                    "suggested_allocation": suggested,
                },
                "action_plan": [
                    {"priority": 1, "action": "Reduce AAPL from 35% to 12%",
                     "reason": "Single-stock concentration exceeds 10% limit by 25 percentage points",
                     "impact": "Reduces portfolio VaR by 4.2%"},
                    {"priority": 2, "action": "Increase BND from 5% to 25%",
                     "reason": "Fixed income severely underweight for moderate risk profile",
                     "impact": "Reduces overall volatility by 35%"},
                    {"priority": 3, "action": "Add VXUS at 15% for international exposure",
                     "reason": "Zero international diversification creates geographic concentration risk",
                     "impact": "Improves diversification ratio by 40%"},
                    {"priority": 4, "action": "Reduce total Tech sector from 90% to 35%",
                     "reason": "Sector concentration well above 40% moderate-risk maximum",
                     "impact": "Reduces sector-specific drawdown risk by 55%"},
                    {"priority": 5, "action": "Add GLD (8%) and TIP (7%) as inflation hedges",
                     "reason": "No real assets or inflation protection in current portfolio",
                     "impact": "Improves risk-adjusted returns in inflationary scenarios"},
                ],
                "estimated_rebalancing_cost": "$1,250 (estimated trading fees and spread)",
                "tax_considerations": "Selling AAPL/MSFT may trigger capital gains — consider tax-loss harvesting opportunities",
                "composition_log": "\n".join(self.loader.composition_log),
            }
        }

        self._print_phase("PHASE:PLAN", "Actions: 5 | Est. improvement: +90% risk-adjusted return")
        print()
        print("Output (JSON):\n")
        print(json.dumps(report, indent=2))
        print(f"\n{'='*70}")
        print(f"  Demo complete. This was a demonstration with sample data.")
        print(f"  The dependency resolution and composition logs above are real.")
        print(f"{'='*70}\n")


class SkillRunner:
    """
    Runs a skill against real input via the Claude API.
    Requires: pip install anthropic + ANTHROPIC_API_KEY env var.
    """

    def __init__(self, loader: SkillLoader):
        self.loader = loader

    def run(self, skill_name: str, input_path: str, model: str = "claude-sonnet-4-20250514"):
        # Check for anthropic SDK
        try:
            import anthropic
        except ImportError:
            print("\n❌ The 'anthropic' package is not installed.")
            print("   Install it with: pip install anthropic")
            print(f"\n💡 Try the demo instead: python loader.py {skill_name} --demo\n")
            return

        # Check for API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("\n❌ ANTHROPIC_API_KEY environment variable not set.")
            print("   Export it with: export ANTHROPIC_API_KEY=sk-...")
            print(f"\n💡 Try the demo instead: python loader.py {skill_name} --demo\n")
            return

        # Read input file
        input_file = Path(input_path)
        if not input_file.exists():
            print(f"\n❌ Input file not found: {input_path}")
            return

        with open(input_file, "r", encoding="utf-8") as f:
            user_input = f.read()

        # Compose system prompt
        print(f"\n🔧 Composing context for {skill_name}...")
        system_prompt = self._clean_compose(skill_name)
        print(f"   Context ready ({len(system_prompt) // 4} tokens)")

        for log_line in self.loader.composition_log:
            print(f"   {log_line}")

        print(f"\n🚀 Sending to Claude ({model})...\n")
        print("-" * 70)

        # Stream response
        client = anthropic.Anthropic(api_key=api_key)
        with client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Analyze the following input:\n\n```\n{user_input}\n```"}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)

        print(f"\n{'-'*70}")
        print(f"\n✅ Done. Skill: {skill_name} | Input: {input_path}\n")

    def _clean_compose(self, skill_name: str) -> str:
        context = self.loader.compose_context(skill_name)
        return _build_clean_prompt(context, skill_name, self.loader)


def _build_clean_prompt(raw_context: str, skill_name: str, loader: SkillLoader) -> str:
    """Strips frontmatter and HTML comments, adds section delimiters and preamble."""
    # Strip YAML frontmatter blocks: --- followed by lines with key: value, ending with ---
    cleaned = re.sub(
        r'(?m)^---\n(?=\w+:)(.*?\n)---\n?', '', raw_context, flags=re.DOTALL
    )
    # Strip standalone --- horizontal rules
    cleaned = re.sub(r'(?m)^---\s*$', '', cleaned)
    # Strip HTML comment markers but keep labels readable
    cleaned = re.sub(r'<!-- DEPENDENCY: (.*?) -->', r'─── DEPENDENCY: \1 ───', cleaned)
    cleaned = re.sub(r'<!-- END: (.*?) -->', r'─── END: \1 ───', cleaned)
    cleaned = re.sub(r'<!-- MAIN: (.*?) -->', r'─── MAIN SKILL: \1 ───', cleaned)
    # Remove any remaining HTML comments
    cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
    # Collapse 3+ blank lines into 2
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    skill = loader.loaded_skills.get(skill_name)
    version = skill.version if skill else "unknown"
    total_tokens = len(cleaned) // 4

    preamble = (
        f"# System Prompt — {skill_name}@{version}\n"
        f"# Generated by Agent Skills Loader v3.0\n"
        f"# Token estimate: ~{total_tokens}\n"
        f"# Skills composed: {len(loader.loaded_skills)}\n\n"
    )
    return preamble + cleaned.strip() + "\n"


def main():
    """CLI principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Agent Skills Loader v3.0 - OOP Dependencies + Progressive Loading"
    )
    parser.add_argument("skill", nargs="?", help="Nome da skill")
    parser.add_argument("--list", "-l", action="store_true", help="Lista skills")
    parser.add_argument("--tree", "-t", action="store_true", help="Árvore de dependências")
    parser.add_argument("--compose", "-c", action="store_true", help="Compõe contexto")
    parser.add_argument("--clean", action="store_true", help="Gera system prompt limpo (usar com --compose)")
    parser.add_argument("--lockfile", action="store_true", help="Gera lockfile")
    parser.add_argument("--demo", action="store_true", help="Executa demonstração com dados de exemplo")
    parser.add_argument("--run", action="store_true", help="Executa via Claude API (requer anthropic + API key)")
    parser.add_argument("--input", help="Arquivo de input para --run")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Modelo Claude para --run")
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
            if args.clean:
                context = _build_clean_prompt(context, args.skill, loader)
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

    if args.demo:
        try:
            demo = DemoRunner(loader)
            demo.run(args.skill)
        except ValueError as e:
            print(f"❌ Erro: {e}")
        return

    if args.run:
        if not args.input:
            print("\n❌ --run requires --input <file>")
            print(f"   Example: python loader.py {args.skill} --run --input examples/samples/vulnerable_app.py\n")
            return
        try:
            runner = SkillRunner(loader)
            runner.run(args.skill, args.input, model=args.model)
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
