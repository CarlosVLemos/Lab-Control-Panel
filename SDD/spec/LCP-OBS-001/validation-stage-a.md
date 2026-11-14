# LCP-OBS-001 — Validação da Etapa A

**Estado:** implementação e testes preparados; execução sob controle do operador.
**Branch:** `feat/lcp-obs-001-stage-a`
**Commit:** commit local final informado no handoff (o SHA não pode ser inscrito no próprio commit).

## Escopo implementado

- Modelo TypeScript somente leitura para o envelope normalizado `lcp.observation.v1`.
- Parser defensivo de texto JSON, sem propagação de exceções de entrada inválida.
- Limites de 5 MiB em bytes UTF-8 e 10.000 eventos, sem truncamento silencioso.
- Validação de campos obrigatórios, enums, sequências, números, timestamps, identidades e hierarquia.
- Normalização de opcionais ausentes para `null`, descarte de campos arbitrários e de `reasoning_content`.
- Preservação da duração total reportada e aviso quando diverge de timestamps comparáveis.
- Proveniência `self_report` explicitamente sinalizada e lista vazia aceita com aviso.
- Fixture exclusivamente sintética, identificada como não medida.

Não foram implementados adaptador AgentTrace, agregações de métricas, UI, backend, persistência ou qualquer item das Etapas B, C ou D.

## Matriz preparada

| test_id | command | environment | exit_status | result | notes |
| --- | --- | --- | --- | --- | --- |
| C01–C10 | `cd frontend && npm test -- src/domain/observation.test.ts` | Dependências frontend providas pelo operador | — | `NOT_RUN` | Testes focados escritos em `src/domain/observation.test.ts`; execução proibida nesta sessão. |
| regressão frontend | `cd frontend && npm test` | Dependências frontend providas pelo operador | — | `NOT_RUN` | Executar somente se o operador desejar ampliar o Gate A. |
| checagem TypeScript/build | `cd frontend && npm run build` | Dependências frontend providas pelo operador | — | `NOT_RUN` | Inclui `vue-tsc -b` e Vite; não executado por restrição operacional. |

## Riscos e pendências

- `detail` é preservado como texto não confiável, sem interpretação. A renderização escapada pertence à Etapa D e não foi implementada aqui.
- A comparação entre `total_duration_ms` e timestamps usa o intervalo exato em milissegundos; qualquer divergência gera aviso e nenhum valor é substituído.
- Não há soma de tokens, custos ou durações de eventos nesta etapa.
- O Gate A permanece aberto até o operador fornecer os resultados reais. `NOT_RUN` não representa aprovação nem falha.
