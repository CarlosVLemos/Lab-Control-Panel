> **AVISO HISTÓRICO — 2026-11-14:** o conteúdo abaixo representa o estado em 11/11/2026, **não** o estado atual. As PRs #37, #39, #42, #44, #46 e #47 foram integradas à `main` em 11–13/11; a PR #41 permanece aberta. O estado atual de planejamento está em [LCP-OBS-001](../SDD/spec/LCP-OBS-001/spec.md) e [ADR-004](architecture/ADR-004-import-first-agent-observability.md). Não executar comandos históricos abaixo sem revisar branch e contexto.

# Lab Control Panel — Estado do projeto e handoff

**Data de corte:** 2026-11-11  
**Repositório:** https://github.com/CarlosVLemos/Lab-Control-Panel  
**Natureza:** registro factual para continuidade em outra conversa; **não** é declaração de prontidão para produção.  
**Fonte:** estado do GitHub consultado nesta data, execução GitHub Actions e observações locais fornecidas pelo usuário. Informações locais não foram verificadas remotamente.

## 1. Estado executivo

O Lab Control Panel (LCP) é uma proposta para **avaliar comparativamente a qualidade, a eficiência, o custo e a confiabilidade de execuções de sistemas/agentes de IA**, incluindo tarefas de resposta, execução de tarefas e geração de código. O recorte atual é um **MVP demonstrativo de comparação Response** com classificadores por regras e dataset sintético; não é, ainda, a plataforma ampla projetada.

**Estado atual:** o primeiro fluxo de ponta a ponta foi implementado e testado na branch `feat/lcp-mvp-end-to-end-demo`. O usuário confirmou em conversa que conseguiu abrir o frontend local e executar a comparação após trocar para a branch correta. **A PR #37 continua aberta em Draft, sem merge; a `main` ainda não contém a integração HTTP/DB/UI dessa PR.**

## 2. Git e entregas

| Parte | Estado | Evidência |
| --- | --- | --- |
| Contratos e invariantes Pydantic (LCP-001) | Integrado à `main` | PR #26; domínio de Project, DatasetVersion, CandidateVersion, Experiment, ExecutionRun, EvaluationResult e PolicyDecision |
| Governança SDD e papéis de agentes | Integrado | PRs #28 e #30; Jarvis, Maquiavel, Van Gogh, Mefisto |
| Persistência PostgreSQL (LCP-002) | Integrado à `main` | PR #31; commit `b0d1533`; sete tabelas, SQLAlchemy, Alembic, transações, fingerprints, concorrência CAS |
| Núcleo Response sintético | Integrado à `main` | PR #35; commit `e0e589c`; seis casos, baseline e candidato determinísticos, avaliador por ground truth |
| UI Vue 3/Vite/TypeScript | Integrado à `main` | PR #34; commit `0fbb28d`; tabela de casos, scores, detalhes, estados de carregamento/erro/vazio |
| Integração ponta a ponta | **Implementada, não integrada** | PR #37, Issue #36; commits de implementação `b61ede7` e `b50d3cb`; permanece Draft |
| Kubernetes, LLM real, avaliação Code/Task, portfólio final | Não implementados neste recorte | Roadmap existente; não afirmar prontidão |

**Referência da `main` no corte:** `0fbb28d8361c60fce18352fe10023fb5f3ede1df`.  
**Referência do código funcional da PR #37:** `b50d3cb4d264f1b8f934e664494e699a3a9b6ed5`.  
Um commit posterior apenas de documentação pode atualizar a cabeça da PR; verificar `git log` antes de analisar testes atribuídos a um SHA.

## 3. Comportamento implementado da PR #37

- Três serviços Docker Compose: **PostgreSQL 16, FastAPI e frontend Vue/Vite**. O frontend é servido por Vite em modo de desenvolvimento no container; não é um deploy web de produção.
- Alembic tem migração inicial `0001 (head)`; executar `alembic upgrade head` explicitamente. O Compose não deve ser interpretado como executor automático de migrações.
- `POST /api/demo/experiments`: cria de forma transacional o experimento de demonstração com projeto, dataset versionado, versões de candidatos, runs e avaliações. Responde com relatório JSON. O cenário e o ID do experimento são fixos; chamadas sequenciais repetidas **recuperam o experimento já salvo**, não executam repetidamente uma nova avaliação.
- `GET /api/demo/experiments/demo-support-intents-v1`: reconstrói um relatório dos registros armazenados, sem chamar o classificador outra vez. O campo `passed` é recomputado comparando saída armazenada com expectativa; **não** é uma releitura completa de decisões de política.
- Dataset: `support-intents/v1`, **seis exemplos sintéticos** de intenção de atendimento. Baseline **2/6**, candidato **6/6**. Esses números são de classificadores de regras sobre dados controlados, **não** medem qualidade de IA/LLM em produção.
- A UI usa o endpoint HTTP no fluxo padrão. Fixture offline somente com `VITE_DEMO_OFFLINE=true`. Falhas da API são exibidas, sem fallback invisível.
- Ainda não há análise real de agentes, métricas econômicas confiáveis, runs estatísticas, execução de código externo, autenticação/RBAC, política automatizada de release ou deploy Kubernetes.

## 4. Verificações e evidências

**GitHub Actions no commit `b50d3cb`:**  
- PR: https://github.com/CarlosVLemos/Lab-Control-Panel/actions/runs/43029866435 — **SUCCESS**, jobs de backend e frontend.  
- Push: https://github.com/CarlosVLemos/Lab-Control-Panel/actions/runs/43029856764 — **SUCCESS**.  
- Backend: **43 testes pytest aprovados, 1 warning** no ambiente CI com PostgreSQL.  
- Frontend: **5 testes Vitest aprovados**, `npm run build` aprovado.  
- `docker compose config -q` aprovado.  
- Smoke: Compose sobe, `alembic upgrade head`, POST executado, validação de seis casos, reinício da API com espera de saúde, GET e comparação exata dos arquivos de resposta; check da porta do frontend aprovado.
- O ambiente local utilizado pelo Codex **não concluiu pytest** por problema no bootstrap de dependências. Esse resultado local é **NOT_RUN**, não FAIL. O CI executou os testes.

**Observações fornecidas pelo usuário, não verificadas de forma independente:**  
- Docker local PostgreSQL Healthy, API iniciada, Alembic `0001 (head)` e oito relações SQL (sete tabelas de domínio + `alembic_version`) foram mostrados antes da integração.
- Frontend abriu em `http://localhost:5173`; o primeiro clique produziu 404 ao rodar código da `main` ainda sem endpoints.
- Após checkout da branch `feat/lcp-mvp-end-to-end-demo` e rebuild dos serviços, o usuário informou **“agora funcionou”**. Não há neste registro captura da tela **pós-execução** ou teste automatizado de interação em navegador. O smoke CI testa HTTP e disponibilidade do frontend, não Playwright/E2E do navegador.

## 5. Limites e riscos técnicos abertos

1. **Gestão de conexões:** `backend/app/api/demo.py` instancia um novo SQLAlchemy `Engine` por chamada de API sem ciclo de vida/dispose explícito. Deve virar dependência/engine de aplicação reutilizável antes de uso prolongado ou carga.
2. **Idempotência sob corrida:** POSTs simultâneos na criação inicial podem resultar em **409** explícito; idempotência sequencial foi testada, concorrente não é garantida.
3. **Escopo fixo do demo:** apenas um experimento e um dataset sintéticos; botão “Executar comparação” pode apenas recuperar o resultado armazenado após a primeira chamada. Não confundir com execução nova a cada clique.
4. **Integridade/imutabilidade:** a LCP-002 valida referências e append-only pelo caminho dos repositórios; não é proteção contra escrita SQL direta por agente privilegiado.
5. **Evidências e métricas:** referências sintéticas de saída/ground truth não são arquivos externos auditados; custo/tokens/duração armazenados como zero sintético não devem ser divulgados como medidas observadas.
6. **E2E visual ausente:** testes Vue e smoke de servidor não equivalem a teste automatizado de clique real no browser.
7. **Publicação/deploy:** frontend via Vite dev server, Compose local e sem autenticação. Nenhuma evidência de ambiente produção, TLS, segurança de execução de terceiros, K8s ou operação pública.
8. **Documentação:** README final de portfólio, vídeo, arquitetura de apresentação e comprovação de `kind`/Kubernetes continuam pendentes.

## 6. Contexto de decisões de engenharia

- **MVP mínimo, demonstrável e honesto:** priorizar fatia vertical funcional, não “perfeição” ou introdução de tecnologias somente para currículo.
- Após excessivas revisões de contrato, o escopo da persistência foi congelado em **MVP v4**, com sete tabelas e validação PostgreSQL. SECURITY DEFINER, triggers avançados e políticas complexas foram adiados.
- Uso de agentes: **Jarvis** para coordenação, **Maquiavel** backend/integração, **Van Gogh** UI, **Mefisto** revisão independente. Specs curtas, execução e evidência real.
- A demonstração atual é deliberadamente **mock/sintética**. Kubernetes deve vir depois de produto funcional; evitar Redis, workers, canary, Argo, LLM-as-judge e Code runner no MVP inicial se não houver necessidade concreta.
- O usuário prefere avaliação técnica independente e análise de trade-offs, sem concordância automática.

## 7. Próximos passos sugeridos (em ordem)

1. **Revisão final e decisão humana sobre PR #37.** Não houve autorização de merge nesta etapa. Checar CI e SHA atuais, corrigir somente bloqueadores concretos; integrar se aprovado.
2. **Documentar a demo e testar visualmente o navegador:** screenshot após clicar, fluxo de erro, reinício, instruções reprodutíveis do `README`; adicionar Playwright simples se custo razoável.
3. **Corrigir gestão de Engine e decidir tratamento de concorrência** antes de múltiplos usuários; separar como tarefa pequena se não bloquear o MVP local.
4. **Preparar apresentação de portfólio:** diagrama simples, README e pequeno vídeo de execução, com distinção explícita entre mock e IA real.
5. **Demonstrar containerização/orquestração:** Docker já comprovado; `kind` + Kustomize e smoke Kubernetes local **após** fechar a demo. Não alegar produção.
6. **Evolução do produto:** selecionar um experimento com agentes reais e métricas observáveis para começar a validar a proposta original LCP, em etapa separada do mock inicial.

## 8. Procedimento local seguro para retomar

**Antes de trocar branch, verificar mudanças locais** com `git status`. Não executar `docker compose down -v`: isso remove o volume e seus dados.

```bash
git fetch origin
git switch feat/lcp-mvp-end-to-end-demo
git pull --ff-only origin feat/lcp-mvp-end-to-end-demo
docker compose up -d --build --wait
docker compose exec -T api alembic upgrade head
curl http://localhost:8000/health
curl -i -X POST http://localhost:8000/api/demo/experiments
curl -i http://localhost:8000/api/demo/experiments/demo-support-intents-v1
```

Frontend: **http://localhost:5173**. API: **http://localhost:8000**. Swagger FastAPI: **http://localhost:8000/docs**. Endereços de loopback, não disponibilização pública.

**Após eventual merge:** `git switch main && git pull --ff-only origin main` e rebuild/recriação dos containers quando apropriado; preservar o volume.

## 9. Ponto de partida para a próxima conversa

> Retome o Lab Control Panel a partir deste documento. Verifique primeiro no GitHub se a PR #37 foi integrada e a CI atual. O MVP Response sintético com Vue, FastAPI e PostgreSQL foi implementado e comprovado na CI, e o usuário relatou execução local bem-sucedida. A PR #37 estava em Draft e não integrada à main no corte. Priorize a conclusão/merge autorizado da integração, correções pontuais e a apresentação de portfólio. Não retome ciclos extensos de planejamento, não confunda mock com avaliação real de IA, nem afirme Kubernetes implementado.
