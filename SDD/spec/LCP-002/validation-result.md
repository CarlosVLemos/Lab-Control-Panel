# LCP-002 — Evidências de implementação

Contrato MVP v4 FROZEN, CR-001. Base `7987b65c8054ccaab522817ffd7b5919c1c2dec9`. Este registro acompanha o código testado no mesmo commit.

| Gate | Resultado observado |
| --- | --- |
| M-01 | PASS. Em schemas vazios, /health deixou o banco sem tabelas e Alembic upgrade head duas vezes criou sete tabelas mais a versão Alembic. |
| M-02 | PASS (CI). Um projeto persistiu no teste local após restart do PostgreSQL 16.2; o GitHub Actions também executou Compose up → Alembic upgrade → INSERT em projects → Compose down/up sem remover volume → SELECT do mesmo ID, com resultado de etapa SUCCESS. Docker segue NOT_RUN na máquina local. |
| M-03 | PASS. Reconexão preservou ordem e fingerprints. Hash inválido e payload corrompido produziram SnapshotIntegrityError. |
| M-04 | PASS. UNIQUE, FK, enums e checks de custo. A violação de UNIQUE reverteu a transação. |
| M-05 | PASS. Candidatos ausentes, de outro projeto ou workload e casos fora do dataset foram rejeitados. |
| M-06 | PASS. Regras de PASS e avaliação inexistente foram verificadas. Avaliação e decisão persistiram em outra sessão, com IDs repetidos preservados. |
| M-07 | PASS. Duas sessões chegaram ao UPDATE com a mesma revisão. Uma atualizou e outra recebeu ConcurrencyConflict. |
| M-08 | PASS. Métricas JSONB em strings exatas, custo com 20 casas, NULL distinto de zero e rejeição de valores JSONB não representáveis. |
| M-09 | PASS (CI). GitHub Actions para commit `ba2e5d566b52efd7dc981c0663148cacf4f80b91`: backend pytest, `docker compose config -q` e o smoke do restart/persistência em Compose concluídos com sucesso. Testes e Compose locais continuam com evidências separadas. |
| M-10 | PASS. [Revisão independente de Mefisto](review.md). |

## Comandos locais

- Em `backend`, `LCP_TEST_DATABASE_URL=postgresql://agent@127.0.0.1:55432/lcp_test PYTHONPATH=/tmp/lcp-deps python -m pytest -q`. Exit 0, 22 passed, um aviso de depreciação do TestClient do Starlette.
- No banco descartável, `python -m alembic upgrade head` e `python -m alembic check`. Exit 0 e `No new upgrade operations detected`.
- `pg_ctl restart` do cluster descartável seguido de consulta do ID `restart-smoke`. Exit 0 e o ID voltou após o reinício.

## Uso e limites

Na raiz, executar `docker compose up --build --wait` e depois `docker compose exec -T api alembic upgrade head`. A API responde em `http://localhost:8000/health`. As operações de persistência são internas ao backend.

Imutabilidade e validações entre agregados ficam no repositório, conforme CR-001. Evidências externas e versão de política são referências opacas. As migrações de validação foram executadas somente em bancos descartáveis.

## Validação remota posterior ao relatório inicial

- **Commit verificado:** `ba2e5d566b52efd7dc981c0663148cacf4f80b91` (correção apenas da configuração do CI após o commit de implementação `5229ca1`).
- **Pull request CI:** https://github.com/CarlosVLemos/Lab-Control-Panel/actions/runs/43018545348 — `completed/success`. O job `backend` registrou sucesso para instalação, `cd backend && python -m pytest -q`, `docker compose config -q` e `Verify Compose restart and persistence`.
- **Push CI:** https://github.com/CarlosVLemos/Lab-Control-Panel/actions/runs/43018536637 — `completed/success`.
- **O que o smoke prova:** uma linha criada em `projects` continuou disponível após `docker compose down` seguido de `docker compose up --wait`, sem `down -v`; API/DB foram iniciados pelos containers na CI. Não prova alta disponibilidade, recuperação de desastre ou deploy Kubernetes.
- **Observação:** a execução local de Docker permanece `NOT_RUN`. Os valores PASS para M-02/M-09 referem-se exclusivamente à evidência remota da CI, não a testes locais inventados.
