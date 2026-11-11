# CR-001 — Simplificação do MVP

**Decisão:** aprovada por orientação explícita do usuário em 2026-11-11: “Faça” a simplificação e priorize “um mvp mínimo ... não ... perfeito”, útil para demonstrar Docker, Kubernetes e engenharia no portfólio.

**Substitui:** DRAFT v3 (`64429c2`) por **MVP v4 FROZEN**.
**Motivo:** três rodadas de revisão da persistência sem código executável criaram custo superior ao benefício esperado.

## Removido da LCP-002
Funções SECURITY DEFINER, papéis customizados, triggers de fechamento, FKs circulares/compostas, tabelas de associação, imutabilidade contra SQL direto, fingerprint de PolicyVersion, executor LLM/Code, Kubernetes e orquestração de workers.

## Mantido
PostgreSQL, Alembic, SQLAlchemy, FK/UNIQUE/CHECK essenciais, transações, JSONB com ordem preservada, fingerprint da LCP-001 na entrada e saída, controle CAS de runs, testes reais em PostgreSQL, Docker Compose, CI e revisão do código executado.

**Limite aceito:** o banco do MVP é acessado somente pelo serviço confiável. Integridade entre projeto/candidato/caso e append-only são garantias dos repositórios, não contra um operador com SQL direto. Evidências externas são opacas e não autorizam promoção automática.

Mudanças de autenticação, execução não confiável, migração de dados reais e contrato público exigem Change Request nova. Correções pequenas para passar testes dentro deste contrato não reabrem o planejamento.
