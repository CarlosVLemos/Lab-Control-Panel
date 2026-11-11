# LCP MVP — Integração executável (Issue #36)

**Owner:** Maquiavel (integração full-stack, SINGLE_WRITER) · **Review:** Mefisto · **Track:** STANDARD
**Branch:** `feat/lcp-mvp-end-to-end-demo` · **Base:** main consolidada com PRs #31, #35 e #34
**Estado:** implementado e revisado; decisão humana de merge pendente. **Não** fazer merge automaticamente.

## Objetivo concreto

Tornar a interface Vue uma demonstração **realmente conectada**, usando o núcleo Response determinístico e os repositórios PostgreSQL já integrados. Uma ação deve executar uma comparação baseline vs candidato sobre os seis casos, persistir e permitir recuperá-la após restart.

## Instruções ao Codex

1. Leia `AGENTS.md`, `SDD/rules.md`, `docs/MVP_DEMO_PLAN.md`, [Issue #36](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/36), `backend/app/domain/models.py`, `backend/app/repositories/persistence.py`, `backend/app/evaluation/response.py`, `backend/app/demo/response_fixture.py`, `frontend/src/domain/report.ts`, `frontend/src/App.vue`.
2. Implemente endpoint **POST /api/demo/experiments** para gerar experimento **sintético determinístico**, persistir as entidades compatíveis com a LCP-001 em **uma transação**, e retornar o ID; **GET /api/demo/experiments/{id}** deve recuperar resultados persistidos — não recalcular fixture nem retornar dados locais quando DB falhar.
3. Preste atenção: o DTO do comparador é simplificado e diferente dos modelos Pydantic de Run/Evaluation/Decision. Mapeie explicitamente e persista dados honestos. Se o contrato exigir evidências para PASS, forneça evidência de ground truth verificável no próprio experimento e rotule-a como sintética; **não** invente artefato externo ou veredito PASS de release. Não force decisão de política se o produto ainda não tiver evidência de política executável; registre essa limitação sem fingir completude.
4. Trate idempotência: POST repetido não duplica nem sobrescreve snapshots/IDs históricos; devolva o mesmo experimento/resultado apenas se a operação for semanticamente equivalente, ou use IDs exclusivos por execução. Nunca esconder `IntegrityError` ou converter exceção em sucesso.
5. Alinhe frontend com API: `HttpReportSource`, URL configurável via proxy Vite/local, loading/error/empty; falha de adapter deve ser renderizada como saída indisponível, nunca PASS. Remova números e textos fixos de cinco casos e substitua a fixture por dados HTTP no fluxo real, mantendo modo offline **explicitamente** separado.
6. Compose deve levantar **PostgreSQL + FastAPI + Vue** de forma reproduzível. Alembic continua migração explícita. Não depender de segredos reais nem usar CORS aberto sem necessidade; priorize proxy reverse ou Vite configurado.
7. CI executa **pytest PostgreSQL real + frontend npm ci/test/build**, smoke HTTP POST/GET e restart do container (sem apagar volume). Criar teste que comprova **GET após reinício sem reexecutar o classificador**; uma interrupção do DB deve produzir erro explícito.
8. Execute testes, corrija falhas reais e registre comandos/resultados/limitações no PR. Quando houver suporte real a Mefisto, solicitar revisão independente sobre diff executável.

## Allowed paths

`backend/app/api/**`, `backend/app/services/**`, `backend/app/main.py`, `backend/tests/**`, `frontend/**`, `docker-compose.yml`, `backend/Dockerfile` (somente se necessário), `.github/workflows/ci.yml`, `docs/tasks/mvp-e2e-demo.md`, `docs/MVP_DEMO_PLAN.md` (atualização mínima).

## Protected / fora de escopo

Não alterar `backend/app/domain/**`, migrações/schema LCP-002, repositórios LCP-002, agentes/SDD/README, Kubernetes, workers, LLM externo, autenticação e avaliação de políticas de produção **sem Change Request específica**.

## Aceite

- HTTP POST executa motor real determinístico e salva; HTTP GET carrega resultado no PostgreSQL com os seis casos, scores 2/6 e 6/6 derivados das saídas.
- Vue usa API real e lida com falha/resultado vazio sem fallback disfarçado.
- Banco reiniciado mantém os resultados; erro do backend não retorna fixture silenciosa.
- Docker Compose em três serviços; CI PostgreSQL + Vue + HTTP smoke; hashes e contratos LCP-001 preservados.
- Mefisto relata limitações (mock não é LLM real, não há release automático). PR sem merge.

**Não abrir outra rodada abstrata de planejamento.** Implemente, teste e apresente problemas reproduzíveis se houver um bloqueio real.

## Evidência de implementação (2026-11-11)

- `POST /api/demo/experiments` executa o comparador determinístico uma vez e persiste
  projeto, snapshots, experimento, doze runs e avaliações numa única transação. Repetir
  a operação reutiliza o experimento sem recalcular ou sobrescrever o histórico.
- `GET /api/demo/experiments/demo-support-intents-v1` reconstrói o DTO a partir dos
  snapshots e saídas registradas nos runs; não chama a fixture/classificadores.
- Checks observados: `npm test` (5 testes aprovados), `npm run build` (aprovado),
  `docker compose config -q` (aprovado), e smoke Compose com `alembic upgrade head`,
  POST/GET e restart da API (relatórios idênticos; 6 casos, baseline 2/6, candidato 6/6).
- A execução local de `pytest` requer ambiente Python com dependências de desenvolvimento;
  o ambiente do agente bloqueou a instalação persistente delas. O CI permanece configurado
  para executar a suíte com PostgreSQL real, incluindo os novos testes HTTP.
- Revisão independente Mefisto: a falha reproduzida de restart no CI foi corrigida ao
  aguardar `docker compose up --wait` antes de Alembic/GET; o smoke corrigido passou.
  Permanecem como restrições a suíte pytest local não executada e o comportamento explícito
  `409` em uma rara corrida entre POSTs simultâneos.

Limitações: os adaptadores e a ground truth são sintéticos e determinísticos; tokens,
custo e duração são marcados como mock/zero. Nenhuma decisão de política de release é
emitida ou inferida.
