# LCP-OBS-001 — Plano de etapas e gates

**Estado:** Etapas A e B validadas pelo operador; B com parecer Mefisto `passed`. Etapa C tem contrato proposto e tarefa preparada **aguardando autorização do operador**; Etapas D/E bloqueadas.
**Alvo de produto:** MVP demonstrável no sábado 14/11/2026, sujeito à execução de testes pelo operador e a decisões de deploy separadas.

## Preparação (documental)
- Revisar ADR-004, spec, contract, tests e [source-agenttrace.md](source-agenttrace.md); amostra AgentTrace já produzida no Atlas e inspecionada pelo revisor; a **publicação/redistribuição da amostra ainda não foi autorizada**. O Codex pode inspecionar Git/GitHub CLI e arquivos; não baixar dataset.
- O operador fornece dependências, arquivos e ambiente. Não fazer `pip install`, `npm ci`, `venv`, downloads, builds, `pytest`, `vitest`, `playwright` ou Docker por iniciativa do Codex.
- O envelope v1 e o perfil AgentTrace estão FROZEN conforme [CR-001/CR-002 aprovadas](APPROVALS_2026-11-14.md). Etapa B implementada e validada **somente no clone local**, ainda sem push/merge. A Etapa C tem [proposta de contrato](METRICS_CONTRACT_C_DRAFT.md) e [tarefa pronta](CODEX_TASK_C.md). Não iniciar C sem autorização de execução pelo operador; D/E bloqueadas.

## A — Modelo e validador
**Escopo autorizado:** schema TypeScript, validação runtime e normalização do envelope LCP v1; invariantes de ordenação, nulidade, eventos, duração total reportada e proveniência. Sem UI completa, adaptador AgentTrace, métricas agregadas ou backend. Usar [CODEX_TASK_A.md](CODEX_TASK_A.md).
**Entregáveis:** módulos TypeScript pequenos e fixtures de contrato, testes escritos mas não executados.
**Aceite:** contrato passa as verificações de [tests.md](tests.md), usando execução manual do operador no final da etapa; retornar PASS/FAIL/NOT_RUN conforme observado.

## B — Adaptador externo real
**Pré-condição atendida para desenvolvimento:** o operador gerou uma amostra local, Mefisto inspecionou sua estrutura e o perfil do adaptador foi aprovado via [CR-002](CHANGE_REQUEST-002.md). **Pré-condição de publicação:** revisão humana de atribuição/licença e sanitização antes de versionar ou disponibilizar amostras reais.
**Escopo autorizado:** adaptar uma execução AgentTrace real para o LCP v1 e ajustar validação pública de `agent.name=null` e `event.position`, sem inventar timestamps/tokens/ferramentas. Instrução: [CODEX_TASK_B.md](CODEX_TASK_B.md).
**Entregáveis:** código, amostra mínima sanitizada permitida, mapeamento campo-a-campo, testes de divergências.
**Aceite:** totais e ordem conferidos ao arquivo fornecido; desconhecidos continuam nulos. Caso amostra não esteja disponível, etapa fica BLOCKED — não baixar substituto silenciosamente.

## C — Métricas de observabilidade
**Escopo proposto:** [contrato de métricas C](METRICS_CONTRACT_C_DRAFT.md): contagens observáveis, duração total com origem, cobertura de uso e tokens acumulados **por etapa LLM** (sem timestamps imaginados), agregação cuidadosa com lacunas, parent/child e cumulatividade. Execução [CODEX_TASK_C.md](CODEX_TASK_C.md) sujeita à autorização do operador.
**Entregáveis:** funções puras TS e testes determinísticos.
**Aceite:** fixtures completas/incompletas/sobrepostas, não duplicação, sem inventar custo/tempo; bateria de testes aplicada **pelo operador ao final**.

## D — Interface de observabilidade
**Escopo:** adicionar aba Observability ao Vue, seletor de arquivo, KPIs, gráfico em degraus, timeline navegável e replay de eventos, detalhes, estados de dados ausentes e erros.
**Entregáveis:** componentes em `frontend/src/**`; preservar Response/Code Evaluation; sem novos serviços.
**Aceite:** usuário importa arquivo real e arquivo declarativo, observa eventos e lacunas, Play/Pause/anterior/próximo funcionam; operador executa build/testes/e2e aprovados ao final.

## E — Fechamento/documentação/deploy separado
**Escopo:** ajustar README e status para refletir apenas funcionalidades demonstradas; preparar instruções de execução estática e descrição de portfólio. Sem instalar ou configurar VPS nesta etapa.
**Aceite:** evidências reais anexadas a PR; Mefisto revisa leitura de código e saídas fornecidas; testes ou builds não executados permanecem `NOT_RUN`; merge, publicação e deploy somente após decisão humana.

## Instrução de colaboração
- Git, `gh`, `git status`, `git diff`, `git log`, `rg`, `cat`, `sed`, leitura e edição de código estão permitidos quando o estágio for autorizado.
- GitHub Actions com `pip install`, `npm ci`, Docker e Playwright também são execução de instalação/teste. Não abrir PR ou fazer push que dispare CI pesada sem aprovação do operador; commits documentais de planejamento devem usar `[skip ci]` quando aplicável.
- O Codex deve **parar** ao terminar a etapa com código e testes preparados, listar comandos para o operador e aguardar os resultados antes de avançar.
- Não rodar tudo "no final do projeto": os testes são **ao final de cada etapa**, por decisão do operador, e regressão final antes da publicação.
- Respeitar o caráter DRAFT dos contratos; não modificar o escopo em silêncio.
