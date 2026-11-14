# CODEX_TASK_C — LCP-OBS-001 · Etapa C: métricas puras

**Situação:** tarefa **preparada** após a Etapa B ter sido aprovada tecnicamente; **a execução desta tarefa depende da autorização do operador ao enviá-la ao Codex**. Consulte [métricas propostas](METRICS_CONTRACT_C_DRAFT.md), [CR-001](APPROVALS_2026-11-14.md), [CR-002](CHANGE_REQUEST-002.md) e [tests.md](tests.md).

## Base local
- Repositório: `/home/carlos/Documentos/www/Ifood/lcp-audit/Lab-Control-Panel`.
- Histórico local da Etapa B: commit de implementação `4de3185be423231169778c0bc4dc45f241e94af0`; commit documental de revisão `1253fb59c28526b13946e85deda6d94700607a93`, segundo relato de Mefisto; ambos **ainda não publicados**.
- A Etapa B passou: 41/41 contrato+adaptador, 1/1 amostra real, regressão 50 PASS/1 SKIPPED (amostra local executada em separado), build PASS; revisão Mefisto `passed`, sem HIGH/MEDIUM/BLOCKER.
- Primeiro inspecione `git status` e commits locais; não rebase/reset/merge destrutivo. Sincronize somente documentação da branch `docs/lcp-obs-001-planning-20261114` **preservando código e histórico local**. `git fetch` de documentação permitido; sem downloads de dataset ou dependências.

## Objetivo
Implementar somente funções **puras de domínio** para métricas de uma execução normalizada, com testes determinísticos que o operador executará. Nenhuma UI, cronômetro, agente, servidor, banco, preço remoto ou telemetria nova.

## Regras mandatórias
1. Leia `AGENTS.md`, `SDD/rules.md`, `SDD/spec/LCP-OBS-001/{spec,contract,tasks,tests,METRICS_CONTRACT_C_DRAFT}.md` e os arquivos `frontend/src/domain/observation*.ts`. Trate contrato A/B como FROZEN. Use [METRICS_CONTRACT_C_DRAFT.md](METRICS_CONTRACT_C_DRAFT.md) como escopo proposto aceito **ao receber autorização do operador**; se surgir divergência semântica nova, pare e reporte, não invente.
2. Criar `frontend/src/domain/observation-metrics.ts` e `observation-metrics.test.ts`. Se desejado, fixtures sintéticas em `__fixtures__`. **Não modificar A/B sem evidência de bug e aprovação adicional**.
3. Produzir contagens por categoria/status e duração reportada/derivada/não disponível com fonte explícita. Não somar durações de span como duração total.
4. Tokens de input/output e curva acumulada **por etapa model** com cobertura completa/ausente; `null` nunca vira zero e lacunas não são ocultadas por valores posteriores. `seq` não é relógio. Não misturar LLM com faixa de spans monotônicos.
5. `final_answer` (message) não é ferramenta operacional. `bash` de exit_code 1 é erro operacional, não prova de qualidade da tarefa.
6. Custo `null` enquanto fonte/preços não comprovados; não inferir por tokens. Origem self_report continua indicada como autorrelato.
7. Se houver hierarquia de usage ambígua ou valores incompletos, total `null`, cobertura/aviso explícitos. Somar somente operações independentes conhecidas.
8. Não registrar payloads brutos em logs e não propagar `detail` hostil para warnings. Garantir determinismo e que métricas não alteram `ObservationRun` original.

## Testes a escrever, mas **NÃO executar**
- Casos M01–M09 da matriz, completos/incompletos/cumulativos, status desconhecidos, ausência de eventos, duração ausente/conflitante, sobreposição de pai/filho e overflow de soma. Checar que erros não geram exceções inesperadas.
- Fixture sintética AgentTrace: 2 model + 1 bash error + 1 final_answer message, totais 3.122 input / 1.439 output / 4.561 total / 15.910931417 s reportado, custo null, série 2 pontos 2.454 e 4.561.
- Teste opcional parametrizado via `AGENTTRACE_SAMPLE_PATH`, usando somente leitura do arquivo real local; não versionar conteúdo privado nem chamar rede.

## Entrega e limites
Pode ler/editar arquivos locais, shell leve, `git/gh`, commits locais. Não instalar/baixar nada, executar testes/builds, criar venv, Docker, browser/E2E, instrumentação, chamadas pagas, push ou PR. Preparar `SDD/spec/LCP-OBS-001/validation-stage-c.md` com matriz `NOT_RUN` e os comandos para o operador. Entregar commit local, escopo, hipóteses, pendências; **PARAR antes da Etapa D**.
