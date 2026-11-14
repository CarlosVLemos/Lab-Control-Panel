# LCP-OBS-001 — Plano de etapas e gates

**Estado: Etapa A autorizada (somente escrita de código/testes); etapas B–E pendentes de gates separados.**
**Alvo de produto:** MVP demonstrável no sábado 14/11/2026, sujeito à execução de testes pelo operador e a decisões de deploy separadas.

## Preparação (documental)
- Revisar ADR-004, spec, contract, tests e [source-agenttrace.md](source-agenttrace.md); fonte AgentTrace selecionada, mas **a amostra real sanitizada depende do operador**. O Codex pode inspecionar Git/GitHub CLI e arquivos; não baixar dataset.
- O operador fornece dependências, arquivos e ambiente. Não fazer `pip install`, `npm ci`, `venv`, downloads, builds, `pytest`, `vitest`, `playwright` ou Docker por iniciativa do Codex.
- O **envelope próprio** foi aprovado FROZEN v1 para Etapa A. O adaptador AgentTrace permanece DRAFT, dependente de amostra real. Não realizar B–E sem novo gate.

## A — Modelo e validador
**Escopo autorizado:** schema TypeScript, validação runtime e normalização do envelope LCP v1; invariantes de ordenação, nulidade, eventos, duração total reportada e proveniência. Sem UI completa, adaptador AgentTrace, métricas agregadas ou backend. Usar [CODEX_TASK_A.md](CODEX_TASK_A.md).
**Entregáveis:** módulos TypeScript pequenos e fixtures de contrato, testes escritos mas não executados.
**Aceite:** contrato passa as verificações de [tests.md](tests.md), usando execução manual do operador no final da etapa; retornar PASS/FAIL/NOT_RUN conforme observado.

## B — Adaptador externo real
**Pré-condição:** operador disponibiliza uma linha real sanitizada do dataset AgentTrace, confirma atribuição/licença e aprova o mapeamento em [source-agenttrace.md](source-agenttrace.md).
**Escopo:** um adaptador único externo que converte a amostra em LCP v1 sem inventar timestamps/tokens/ferramentas.
**Entregáveis:** código, amostra mínima sanitizada permitida, mapeamento campo-a-campo, testes de divergências.
**Aceite:** totais e ordem conferidos ao arquivo fornecido; desconhecidos continuam nulos. Caso amostra não esteja disponível, etapa fica BLOCKED — não baixar substituto silenciosamente.

## C — Métricas de observabilidade
**Escopo:** contagens de eventos/chamadas/erros, duração total observável, uso por chamada, tokens acumulados **por etapa ordinal** (sem timestamps imaginados), agregação ciente de parent/child e cumulatividade.
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
