# ADR-001 — Monólito modular com worker separado

**Status:** Accepted · **Escopo:** MVP

## Contexto

O projeto precisa comparar workloads diferentes, mas compartilhar contratos, política e persistência. Microsserviços independentes criariam overhead de deploy, transações distribuídas e operações antes de haver demanda comprovada.

## Decisão

- Adotar monólito modular Python/FastAPI, com fronteiras explícitas entre domínio, aplicação, API e infraestrutura.
- Manter o domínio independente de FastAPI, banco e SDKs de modelos.
- Executar trabalhos longos em worker separado; a API apenas agenda e consulta.
- Evoluir o armazenamento com PostgreSQL/SQLAlchemy/Alembic e a fila com Redis/RQ em issues próprias.

## Consequências

Simplifica testes e operação inicial. Escalabilidade independente de módulos fica adiada; extrações futuras dependerão de telemetria e necessidade observada, não de especulação.
