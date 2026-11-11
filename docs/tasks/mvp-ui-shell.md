# MVP — Interface de comparação

**Issue:** #32 · **Branch:** `feat/lcp-mvp-ui-shell`
**Owner:** Van Gogh · **Track:** STANDARD · **Modo:** SINGLE_WRITER
**Status:** implementação autorizada, aguardando Codex

## Instrução para Codex

Leia `AGENTS.md`, `SDD/rules.md`, `docs/MVP_DEMO_PLAN.md` (na branch LCP-002, se ainda não estiver na main) e [Issue #32](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/32) completa. Implemente a página de demo sem nova rodada longa de planejamento.

**Pode editar:** `frontend/**`, este arquivo. **Não** alterar backend, CI, Compose, SDD ou README. Os testes e o build do frontend são sua responsabilidade.

## Uma tela, não vinte

Layout profissional e responsivo, com comparação baseline/candidato, status de casos, filtros simples e detalhe por caso. Estados de carregamento/erro/vazio. Dataset claramente sintético, score derivado da fixture. Não simular métricas reais de token/latência/custo. Contrato TypeScript alinhado ao JSON da Issue #32 e adaptador de fonte de dados substituível pela futura API.

## Verificação

`npm ci`, `npm run build` e testes criados. Se criar scripts de teste, inclua-os em `package.json`. Anote comandos, resultados e possíveis limitações; PR Draft contra main e sem merge.

## Handoff

Descreva como executar, estados contemplados, contrato dos dados e como substituir a fixture por HTTP. Use PR separado para evitar conflitos com a tarefa #33.
