# LCP-002 — Tarefas executáveis

**Mode:** SINGLE_WRITER · **Contrato:** FROZEN MVP v4 · **Aprovação:** CR-001
**Owner:** Maquiavel (implementação). Mefisto só revisa depois, sem escrever o código que julga.

| Ordem | Entrega | Prova |
| --- | --- | --- |
| T-01 | SQLAlchemy, conexão/sessão, PostgreSQL Compose, Alembic | M-01/02 |
| T-02 | Sete tabelas, JSONB ordenado, mappers Pydantic e constraints | M-03/04/05/08 |
| T-03 | Repositórios transacionais + CAS de runs + fail-closed de decisões | M-05/06/07 |
| T-04 | Testes PostgreSQL, CI, Dockerfile não-root e evidências | M-01..M-10 |
| V-01 | Revisão independente de diff, SQL, tests, regressões e limitações | review.md/validation-result.md |

**Allowed paths:** `backend/app/db/**`, `backend/app/repositories/**`, `backend/app/services/**`, `backend/alembic/**`, `backend/alembic.ini`, `backend/requirements*.txt`, `backend/tests/**`, `backend/app/main.py` (somente wiring mínimo), `backend/Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`, `.github/workflows/ci.yml`, `SDD/spec/LCP-002/**`, `SDD/index.md`.

**Protegidos:** `backend/app/domain/**`, `frontend/**`, `k8s/**`, `README.md`, `AGENTS.md`, `.agents/**`, `SDD/rules.md`.

**Stop conditions:** qualquer banco não descartável para migração destrutiva, escopo externo, alteração da LCP-001, segredos, execução de código arbitrário ou contrato público. Reportar impedimento real; não trocar implementação por especulação.
