# CODEX_TASK_A — LCP-OBS-001 · Etapa A

**Autorização registrada:** desenvolvimento da Etapa A SOMENTE. Contrato do envelope LCP v1 FROZEN. Etapa B/AgentTrace, cálculos agregados da etapa C e UI da etapa D não autorizados nesta tarefa.

## Objetivo
Implementar **somente** o modelo TypeScript, parser/validador defensivo e normalização do envelope `lcp.observation.v1`, com fixtures e testes Vitest escritos mas NÃO executados. O usuário executará a validação.

## Preparação sem downloads nem testes
1. No clone local `/home/carlos/Documentos/www/Ifood/lcp-audit/Lab-Control-Panel`, inspecione `git status` e `git branch` para preservar alterações locais.
2. Obtenha a branch documental `docs/lcp-obs-001-planning-20261114` e parta dela para `feat/lcp-obs-001-stage-a`. Git/`gh`, inspeção e commits locais estão autorizados. Se houver alterações não versionadas, não sobrescrever.
3. Leia `AGENTS.md`, `SDD/rules.md`, `SDD/spec/LCP-OBS-001/{spec,contract,tasks,tests,source-agenttrace}.md`, `docs/architecture/ADR-004-import-first-agent-observability.md`. Considere apenas o envelope v1 como FROZEN.
4. Observe estilo atual em `frontend/src/domain/`, testes Vitest e `frontend/package.json`.

## Arquivos permitidos
- Novo(s) `frontend/src/domain/observation*.ts` e seus testes `*.test.ts`.
- Fixtures pequenas em `frontend/src/data/` ou `frontend/src/domain/__fixtures__/` (somente sintéticas e explicitamente rotuladas).
- `SDD/spec/LCP-OBS-001/validation-stage-a.md` para resumo de implementação/pendências.

Não modificar `frontend/src/App.vue`, `frontend/src/styles.css`, backend, banco, dependências, CI, contrato FROZEN, CODE-001, RAG ou arquivos fora desse escopo.

## Comportamento esperado
- Expor uma API simples e tipada, por exemplo `parseLcpObservation(input: string): ParseResult` e tipos `ObservationRun`, `ObservationEvent`, `ValidationIssue`; erros sem lançar stack trace de input inválido.
- JSON UTF-8 até 5 MiB e máximo de 10 mil eventos; validar antes de contabilizar qualquer execução.
- Campos obrigatórios: `schema_version`, `run_id`, `source.kind/format/producer`, `agent.name`, `events[]` e, por evento, `id/seq/kind/name/status`. Tipo exato `lcp.observation.v1`.
- Preservar `null` em campos opcionais desconhecidos. Aceitar `events: []` com aviso; rejeitar ids/seq duplicados e referências pai/filho inválidas; seq inteiro positivo. Não fabricar timestamps ou eventos.
- Suportar `started_at`, `ended_at` ISO 8601 com timezone e `total_duration_ms` reportado mesmo sem timestamps. Verificar duração reportada não negativa; se divergir de intervalo comparável, avisar sem substituição silenciosa.
- Uso opcional por evento: `input_tokens`, `output_tokens`, `duration_ms` como números finitos não negativos; `cost_usd` decimal textual válido ou null. Sem converter ausência em zero.
- `source.kind`: `trace|self_report|fixture`; `event.kind`: `model|tool|message|system`; `event.status`: `success|error|unknown`.
- Não transportar `reasoning_content` nem chaves arbitrárias para o objeto normalizado. `detail` é texto não confiável, sem interpretação HTML/JS, shell ou URL; não registrar payload bruto ou dados sensíveis em logs.
- Não somar tokens, custos ou durations de eventos nesta etapa (serão calculados em C). Sem parser AgentTrace nesta etapa (B).

## Testes de contrato a escrever (NÃO EXECUTAR)
Cobrir `C01` a `C10` de `tests.md`: válido completo, parcial, autorrelato, sem tokens/timestamps, limites de tamanho/contagem, JSON inválido, duplicatas, hierarquias inválidas, números negativos/infinitos, conteúdo hostil, duração total reportada, conflitos de relógio e descarte de `reasoning_content`. Fixtures pequenas; gerar limite de tamanho em memória no teste sem versionar megabytes.

## Limites de execução
**Pode:** ler e editar código, `git`/`gh`, shell leve, commits locais.
**Não pode:** criar venv, baixar/install pacotes, `npm ci/install`, `pip`, executar `npm test`, `vitest`, `vue-tsc`, build, Playwright, Docker, migração, ferramenta externa ou qualquer script de teste. Não fazer push nem abrir PR que dispare CI sem autorização específica do operador. Se faltar dependência, apenas reportar.

## Entrega e parada
Após implementar e escrever os testes, pare. Relate arquivos alterados, SHA de commit local, invariantes implementados, riscos e os comandos de teste para o operador executar; marque todos os testes `NOT_RUN`. **Aguarde o resultado informado pelo operador antes da Etapa B.** Não alegar que o código foi validado sem execução.

A amostra AgentTrace do Atlas está em `/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json`, mas não é necessária para a Etapa A e não deve ser modificada nem usada para inferir contrato adicional.
