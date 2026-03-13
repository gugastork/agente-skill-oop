---
name: financial-rules-base
version: 1.0.0
type: abstract
description: Source of truth for financial analysis rules. Abstract skill — do not invoke directly.
tags: [finance, risk, portfolio, abstract, base]
author: Gustavo Stork
---

# Financial Rules Base

## GUARD

> ⚠️ **SKILL ABSTRATA**
>
> Se você foi invocado diretamente (não via outra skill que declare dependência),
> responda: "Esta é uma skill abstrata. Use `risk-analyzer`, `portfolio-optimizer` ou
> `investment-orchestrator` para tarefas específicas."

## PROPÓSITO

Esta skill é uma **ABSTRAÇÃO**. Ela não executa ações — apenas fornece definições, fórmulas e regras que outras skills devem carregar e aplicar.

---

## [SUMMARY]

### Visão Geral das Regras (~200 tokens)

**Risk Metrics:** Value at Risk (VaR), Conditional VaR (CVaR), Beta,
Standard Deviation, Maximum Drawdown.

**Portfolio Theory:** Modern Portfolio Theory (Markowitz), Efficient Frontier,
Capital Asset Pricing Model (CAPM), Sharpe Ratio.

**Compliance Rules:** Diversification limits, concentration risk thresholds,
liquidity requirements, regulatory constraints.

**Métodos Abstratos:**
- `analyze_risk(portfolio) → RiskReport`
- `optimize_allocation(portfolio) → OptimalAllocation`

---

## [FULL]

### Risk Metrics Detailed

#### Value at Risk (VaR)
- Measures maximum expected loss over a time period at a confidence level
- Parametric VaR: VaR = μ - Zα × σ (assumes normal distribution)
- Historical VaR: Based on actual historical returns
- Monte Carlo VaR: Simulated scenarios
- Standard confidence levels: 95% (1.65σ) and 99% (2.33σ)

#### Conditional VaR (CVaR / Expected Shortfall)
- Expected loss given that VaR has been exceeded
- More conservative than VaR
- Better captures tail risk
- CVaR ≥ VaR always

#### Beta
- Measures systematic risk relative to market
- β = Cov(Ri, Rm) / Var(Rm)
- β > 1: More volatile than market
- β < 1: Less volatile than market
- β = 0: No correlation with market

#### Maximum Drawdown
- Largest peak-to-trough decline
- MDD = (Peak - Trough) / Peak
- Key metric for risk tolerance assessment

---

### [FULL:portfolio]

#### Modern Portfolio Theory (Markowitz, 1952)
- Investors are risk-averse and prefer higher returns for same risk
- Portfolio risk is not sum of individual risks (diversification)
- Efficient Frontier: Set of optimal portfolios offering highest return per risk level
- Optimal portfolio: Tangency point with Capital Market Line

#### Sharpe Ratio
- Risk-adjusted return measure
- Sharpe = (Rp - Rf) / σp
- Where: Rp = portfolio return, Rf = risk-free rate, σp = portfolio std dev
- Higher is better; > 1 is good, > 2 is very good, > 3 is excellent

#### Capital Asset Pricing Model (CAPM)
- E(Ri) = Rf + βi × (E(Rm) - Rf)
- Expected return based on systematic risk
- Risk premium = β × Market premium

#### Asset Allocation Strategies
- Strategic: Long-term target allocation based on goals
- Tactical: Short-term deviations to exploit opportunities
- Dynamic: Adjusts with market conditions
- Constant-proportion: Fixed allocation ratios

---

### [FULL:compliance]

#### Diversification Rules
- No single asset > 10% of portfolio (institutional standard)
- No single sector > 25% of portfolio
- Minimum 5 asset classes for balanced portfolios
- International exposure: 20-40% for developed market investors

#### Liquidity Requirements
- Maintain minimum 5% in highly liquid assets
- Match investment horizon to asset liquidity
- Emergency fund: 3-6 months expenses in liquid assets

#### Regulatory Constraints
- Know Your Customer (KYC) requirements
- Suitability assessment for risk profile
- Reporting obligations for large positions
- Tax-efficient structuring within legal limits

---

## [ABSTRACT] Métodos a Implementar

Skills que "herdam" desta base devem implementar:

```
analyze_risk(portfolio: Portfolio) → RiskReport
  - Recebe composição do portfólio
  - Retorna métricas de risco (VaR, Beta, Sharpe, etc.)
  - Deve classificar nível de risco: Low / Medium / High / Critical

optimize_allocation(portfolio: Portfolio, constraints: Constraints) → OptimalAllocation
  - Recebe portfólio atual e restrições
  - Retorna alocação otimizada via fronteira eficiente
  - Deve respeitar regras de compliance

generate_report(portfolio: Portfolio) → InvestmentReport
  - Recebe portfólio completo
  - Retorna relatório consolidado com análise e recomendações
```

---

## CHANGELOG

- **v1.0.0** (2026-03-13): Initial release with VaR, Sharpe, MPT, compliance rules
