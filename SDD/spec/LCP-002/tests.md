# LCP-002 — Testes do MVP v4

**Validator:** Mefisto · **Implementação:** Maquiavel · **Status:** NOT_RUN (código ainda não executado)
**Ambiente:** PostgreSQL real de CI ou Compose descartável, Python 3.12+.

| ID | Comportamento exigido |
| --- | --- |
| M-01 | Alembic upgrade head em banco vazio e novamente sem erro; API não cria tabelas automaticamente |
| M-02 | API + PostgreSQL via Compose com healthcheck; restart sem apagar volume mantém dados |
| M-03 | Round-trip Project, DatasetVersion (cases em ordem), CandidateVersion em sessões diferentes; fingerprints iguais à LCP-001 |
| M-04 | UNIQUE/FK/CHECK essenciais rejeitam duplicação, órfãos, enums inválidos e custo negativo/não-finito |
| M-05 | Experiment valida mesmo projeto/workload, baseline e challengers; run rejeita case/candidato estranho; nenhum registro parcial |
| M-06 | EvaluationResult e PolicyDecision persistem; PASS sem evidência/falha crítica rejeitado, avaliação faltante rejeitada no repositório |
| M-07 | Duas sessões tentam transição CAS com mesma revision: uma vence, outra dá conflito tipado |
| M-08 | Decimal `0.9500` e `1E-7` em JSON strings; custo >8 casas, NULL vs 0, rejeição de payload JSONB fora de capacidade |
| M-09 | pytest backend, `/health`, `docker compose config -q`, GitHub Actions com PostgreSQL real |
| M-10 | Revisão Mefisto: nenhum segredo, migração destrutiva não autorizada, dado sintético apresentado como medido, claim falsa de imutabilidade |

Registrar exatos comandos, logs e SHA. Gates M-01/03/04/05/06/07/08/09 devem estar PASS; M-02/10 reportados. Ausência de teste = NOT_RUN; não supor PASS por mock/SQLite.

**Limite assumido:** não testar como requisito proteção contra SQL direto com permissões elevadas. Isso é *futuro*, não bloqueio ao MVP.
