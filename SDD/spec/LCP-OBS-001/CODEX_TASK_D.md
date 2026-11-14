# CODEX_TASK_D — Etapa D: Dashboard de observabilidade

**A implementação desta tarefa só está autorizada quando o operador a enviar diretamente ao Codex.** Leia [UI_CONTRACT_D_DRAFT.md](UI_CONTRACT_D_DRAFT.md) e [spec.md](spec.md), `AGENTS.md`, `SDD/rules.md`, `tests.md`, contratos A/B FROZEN e o **contrato C local FROZEN v1**, no histórico do commit `3289cc7dd649225ecf809f3cc1e9b5307811596a`.

## Preparação
1. Clone local `/home/carlos/Documentos/www/Ifood/lcp-audit/Lab-Control-Panel`, branch relatada `feat/lcp-obs-001-stage-a`, commit documental local C `3289cc7dd649225ecf809f3cc1e9b5307811596a`. Inspecione `git status`, `git log`, preserve commits e relatórios A/B/C, **não fazer reset/rebase destrutivo**. Pode derivar branch `feat/lcp-obs-001-stage-d`.
2. Integre a documentação de `origin/docs/lcp-obs-001-planning-20261114` de forma segura. A branch remota **ainda tem cópia histórica DRAFT** do contrato C; **não sobrescreva a versão FROZEN local**. Se houver conflito, preserve a versão aprovada e registre a decisão.
3. Inspecione **assinaturas reais e tipos** em `frontend/src/domain/observation.ts`, `observation-agenttrace.ts`, `observation-metrics.ts` antes de codificar. `App.vue` atual usa `<CodeEvaluationView v-else />` e deve virar seleção explícita em três vias.
4. Somente a implementação da Etapa D está liberada: Vue UI/importação local, KPIs, gráfico ordinal, trilhas e replay de registros. Etapa E/infra/hosting fora de escopo.

## Entrega funcional
- Terceira aba Observability preservando Response e Code Evaluation.
- Importar JSON local nativo `lcp.observation.v1` e AgentTrace (limite 5 MiB, formato explícito, falhas visíveis sem fixture fallback). Sem HTTP/upload.
- Computar métricas pelo módulo C, renderizar contagens, origem, cobertura, duração, tokens/custo nullable, avisos e estado parcial.
- Gráfico acumulado de tokens **por passo LLM**, lacunas sem linha fictícia; sem eixos de tempo inventados.
- Eventos em duas faixas distintas AgentTrace (LLM ordinal e spans monotônicos), outra seção para eventos sem position; `final_answer` exibido como message/unknown. Não alegar cronologia global.
- Play/Pause/Anterior/Próximo por faixa selecionada; avanço visual com intervalo fixo, não reexecução nem reprodução real de duração. Cancela timers ao trocar arquivo/faixa, em unmount e quando reprodução termina.
- Detalhes seguros, texto escapado/truncado, nenhuma execução de código, nenhum dado importado enviado à rede, responsividade e acessibilidade.
- Paginação explícita/janela para 10 mil eventos, sem alterar métricas. Opcional demo sintética claramente rotulada; **não versionar o AgentTrace real**.

## Testes para escrever, NÃO executar
- U01–U10 em `tests.md` com helpers puros Vitest (sem novas dependências) + checklist manual para UI: importação real, invalid/partial, gráfico, replay, troca de faixa, dados hostis, arquivo enorme, mobile/teclado e preservação das outras duas abas.
- `SDD/spec/LCP-OBS-001/validation-stage-d.md` com matriz `NOT_RUN` e comandos recomendados `npm test`, `npm run build`, `npm run dev` para o operador. Não afirmar teste visual/E2E automatizado.

## Execução permitida
Pode inspecionar/editar arquivos, shell leve, git/gh, commits **locais**. **Não pode** instalar pacotes, baixar nada, criar venv, executar testes/build/dev server, Docker, browser/Playwright, migrações, scripts de amostra, chamadas pagas, push/PR, merge remoto ou deploy. Não iniciar E.

## Entrega
Commit local, resumo funcional, arquivos, riscos, casos de teste preparados e comandos para validação do operador; worktree limpo. **PARE** antes de testes ou novos estágios.
