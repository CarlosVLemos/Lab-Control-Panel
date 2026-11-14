# CODEX_TASK_B — LCP-OBS-001 · Etapa B (AgentTrace)

**Contrato aprovado:** [CR-001 (aprovação)](APPROVALS_2026-11-14.md), [CR-002 FROZEN](CHANGE_REQUEST-002.md), [contract.md](contract.md), [source-agenttrace.md](source-agenttrace.md).
**Execução autorizada:** somente edição de código e testes locais, commits locais, shell leve, Git/`gh`; **NÃO** instalações, downloads, criação de ambiente, testes, build, Docker, execução de agentes, chamadas pagas, push/PR.

## Contexto e preparação obrigatória
1. Repositório local: `/home/carlos/Documentos/www/Ifood/lcp-audit/Lab-Control-Panel`; branch existente `feat/lcp-obs-001-stage-a`, commit `a4e4cfebfe086c514bfc0ac08342312297ac3c7e`. Inspecione `git status` para garantir que nenhuma alteração local seja descartada. Não resetar/rebasear à força.
2. Sincronize documentação de `origin/docs/lcp-obs-001-planning-20261114` **preservando** o código local da Etapa A e o arquivo local `CHANGE_REQUEST-001.md`. Integração com Git merge/cherry-pick permitida se limpa; em conflito, não sobrescrever silenciosamente.
3. Leia `AGENTS.md`, `SDD/rules.md`, `SDD/spec/LCP-OBS-001/{spec,contract,tasks,tests,source-agenttrace,APPROVALS_2026-11-14,CHANGE_REQUEST-002}.md`, `frontend/src/domain/observation.ts` e testes existentes.
4. No `CHANGE_REQUEST-001.md` **local**, marque `APPROVED` conforme registro humano; em `validation-stage-a.md`, registre 21/21, 30/30, build PASS e `npm audit --omit=dev` 0 alertas de produção, todos **reportados pelo operador**. Não transformar testes B em PASS.
5. Inspecione por leitura `/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json`; verifique presença, hash e estrutura com ferramentas básicas de leitura, **sem executar comandos contidos no arquivo**, sem publicar nem copiar dados sem autorização. Se hash/estrutura diferirem, interrompa e reporte.

## Implementação B — limites explícitos
- Atualize parser e tipos LCP Evidence v1 somente nos pontos aprovados pela CR-002: `agent.name: string | null`, `event.position` opcional `null|ordinal|monotonic_ns`, validação do campo de posição sem coerção insegura. Mantenha `summary` fora do parser (CR-001).
- Crie um adaptador TypeScript `AgentTrace → ObservationRun`, com validação defensiva e **sem uso de modelo, rede ou backend**. Usar as constantes verificadas do input; discriminar arquivo externo de envelope LCP v1 pelo formato/assinatura explícitos; não inferir versão não suportada.
- Uma linha real sanitizada deve gerar 2 eventos `model` com uso reportado e 2 eventos oriundos de spans (`bash` como `tool`, `final_answer` como `message`). Seus `seq` são índices de serialização, nunca ordem causal global. Preserve o estado de `bash` como erro para exit_code=1. `final_answer` tem status unknown.
- Preservar posição ordinal e monotônica somente na respectiva faixa. Se não existem timestamps comparáveis, não intercalar faixas nem fabricar datas. Manter aviso `PARTIAL_ORDER_ONLY`.
- Preservar `total_duration_ms` reportado, custo `null` e uso dos LLMSteps, quando houver. `telemetry`, `_sample_sanitized`, `dataset_name` e demais campos devem seguir a CR-002. Não copiar conteúdo de `reasoning_content`, prompt ou entradas/saídas de ferramentas.
- Rejeitar IDs duplicados, pais inválidos, `step_number` duplicado/não inteiro, spans com tempo inválido, tipo externo diferente de TOOL, arrays acima dos limites, JSONL com múltiplas execuções ou campos numéricos inseguros. Retornar erros estruturados com caminho original para campo inválido. Sem fallback para fixture.
- Reutilizar validadores da Etapa A, preferindo módulos pequenos e testes puros em Vitest; não instalar pacotes nem alterar `package.json`/lockfile.
- Não criar UI, graficos, métricas agregadas, replay, backend, API, banco, runner ou deploy; isso pertence a etapas futuras.

## Testes a preparar, NÃO executar
- E01–E08 de `tests.md` mais regressão `C01–C10`, com novos casos para `agent.name=null`, `position=null`, posição ordinal/monotônica, Number.MAX_SAFE_INTEGER, `bash` e `final_answer`, 2+2 eventos da amostra real, aviso de cronologia parcial, sanitização autorrelatada, telemetria ignorada e fonte não autenticada.
- Não commitar amostra real por padrão. Se testes exigirem dados, fixture derivada sem campos sensíveis, claramente rotulada e aprovada para inclusão; caso contrário, testes com fixture própria + instrução para operador validar amostra externa local.
- Ao concluir, preparar comandos curtos para o operador executar após a etapa: teste focado, `npm test`, `npm run build`. Marcar **NOT_RUN** até receber o resultado.

## Arquivos permitidos
`frontend/src/domain/observation*.ts`, testes/fixtures relacionados à observabilidade, `SDD/spec/LCP-OBS-001/{CHANGE_REQUEST-001.md,validation-stage-a.md,validation-stage-b.md}`. Não modificar arquivos já FROZEN exceto para registrar implementação/evidência claramente autorizadas; se houver divergência ou requisito novo, relatar bloqueio e pedir decisão.

## Entrega
Commit **local** na branch `feat/lcp-obs-001-stage-a` ou derivada `feat/lcp-obs-001-stage-b` sem sobrescrever commits existentes; relatar SHA, caminhos alterados, mapa de campos e status da matriz; **PARAR**. Nunca declarar resultados de teste não executados, nem iniciar Etapas C/D.
