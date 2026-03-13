---
name: code-standards-base
version: 1.0.0
type: abstract
description: Source of truth for code review standards. Abstract skill — do not invoke directly.
tags: [code-review, security, performance, abstract, base]
author: Gustavo Stork
---

# Code Standards Base

## GUARD

> ⚠️ **SKILL ABSTRATA**
>
> Se você foi invocado diretamente (não via outra skill que declare dependência),
> responda: "Esta é uma skill abstrata. Use `security-auditor`, `performance-optimizer` ou
> `code-review-orchestrator` para tarefas específicas."

## PROPÓSITO

Esta skill é uma **ABSTRAÇÃO**. Ela não executa ações — apenas fornece definições e regras que outras skills devem carregar e aplicar.

---

## [SUMMARY]

### Visão Geral das Regras (~200 tokens)

**OWASP Top 10:** SQL Injection, XSS, CSRF, Broken Auth, Security Misconfig,
Sensitive Data Exposure, XML External Entities, Broken Access Control,
Insecure Deserialization, Insufficient Logging.

**SOLID Principles:** Single Responsibility, Open/Closed, Liskov Substitution,
Interface Segregation, Dependency Inversion.

**Performance Rules:** O(n) complexity awareness, memory management,
I/O optimization, caching strategies.

**Métodos Abstratos:**
- `audit(code) → SecurityReport`
- `optimize(code) → OptimizedCode`

---

## [FULL]

### OWASP Top 10 Detailed

#### 1. SQL Injection
- Never concatenate user input in SQL queries
- Use parameterized queries / prepared statements
- Validate and sanitize all inputs
- Apply least privilege to DB accounts

#### 2. Cross-Site Scripting (XSS)
- Encode output in HTML context
- Use Content-Security-Policy headers
- Validate input on server side
- Use frameworks with auto-escaping

#### 3. CSRF (Cross-Site Request Forgery)
- Implement anti-CSRF tokens
- Validate Origin/Referer headers
- Use SameSite cookie attribute

#### 4. Broken Authentication
- Implement multi-factor authentication
- Use secure password hashing (bcrypt, argon2)
- Session management with secure tokens
- Rate limiting on auth endpoints

#### 5. Security Misconfiguration
- Remove default credentials and configs
- Disable unnecessary features and services
- Keep frameworks and dependencies updated
- Use security headers (HSTS, X-Frame-Options)

#### 6. Sensitive Data Exposure
- Encrypt data at rest and in transit
- Use TLS 1.2+ for all connections
- Never log sensitive data (passwords, tokens)
- Implement proper key management

#### 7. XML External Entities (XXE)
- Disable external entity processing
- Use simpler data formats (JSON) when possible
- Validate and sanitize XML input

#### 8. Broken Access Control
- Deny by default
- Implement proper RBAC/ABAC
- Validate permissions on every request
- Log access control failures

#### 9. Insecure Deserialization
- Never deserialize untrusted data
- Use allow-lists for deserialization
- Implement integrity checks (signatures)

#### 10. Insufficient Logging
- Log all authentication events
- Log access control failures
- Ensure logs have enough context
- Implement monitoring and alerting

---

### [FULL:solid]

#### Single Responsibility Principle
- Each function/class does ONE thing
- If description needs "and", it's doing too much
- Extract until each unit has a single reason to change

#### Open/Closed Principle
- Open for extension, closed for modification
- Use interfaces and abstract classes
- Prefer composition over inheritance

#### Liskov Substitution Principle
- Subtypes must be substitutable for base types
- Don't weaken preconditions or strengthen postconditions
- Maintain behavioral compatibility

#### Interface Segregation Principle
- Many specific interfaces over one general interface
- Clients shouldn't depend on methods they don't use
- Split fat interfaces into focused ones

#### Dependency Inversion Principle
- Depend on abstractions, not concretions
- High-level modules don't depend on low-level modules
- Both depend on abstractions

---

### [FULL:performance]

#### Complexity
- Prefer O(n) or O(n log n) over O(n²)
- Use hash maps for frequent lookups
- Profile before optimizing
- Avoid premature optimization

#### Memory Management
- Minimize allocations in hot paths
- Use object pools for frequent allocations
- Watch for memory leaks (event listeners, closures)
- Prefer streaming over buffering for large data

#### I/O Optimization
- Batch database queries (avoid N+1)
- Use connection pooling
- Implement caching at appropriate layers
- Use async I/O for non-blocking operations

#### Caching Strategies
- Cache at the right level (memory, Redis, CDN)
- Implement proper cache invalidation
- Use TTL-based expiration
- Consider cache warming for cold starts

---

## [ABSTRACT] Métodos a Implementar

Skills que "herdam" desta base devem implementar:

```
audit(code: string) → SecurityReport
  - Recebe código fonte
  - Retorna relatório de segurança com vulnerabilidades
  - Deve verificar OWASP Top 10

optimize(code: string, focus: "performance" | "security" | "all") → OptimizedCode
  - Recebe código e foco de otimização
  - Retorna código otimizado + lista de mudanças

review(code: string) → ReviewReport
  - Recebe código fonte
  - Retorna review completo (segurança + performance + SOLID)
```

---

## CHANGELOG

- **v1.0.0** (2026-03-13): Initial release with OWASP Top 10, SOLID, Performance rules
