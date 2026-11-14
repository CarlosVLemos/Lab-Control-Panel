# LCP-OBS-001 — Aprovações humanas e gates (2026-11-14)

## Registro de decisão explícita

**Aprovador:** operador/proprietário do projeto, em conversa, resposta "sim" à aprovação conjunta da CR-001 e dos ajustes da CR-002.

### CR-001 — Adiar `summary`
**APROVADA.** A estrutura normalizada da Etapa A entrega `runId`, `sourceKind`, `events[]` e `warnings[]`; não calcula nem exige `summary`. A agregação `summary` será definida na Etapa C, a partir de regras verificáveis, com testes próprios. Não inventar valores na Etapa A. O arquivo `CHANGE_REQUEST-001.md` foi criado **na branch local** `feat/lcp-obs-001-stage-a` no commit `a4e4cfebfe086c514bfc0ac08342312297ac3c7e` e precisa ter seu status registrado como aprovado na integração; **não criar outra cópia conflitante na branch documental**.

### CR-002 — Perfil AgentTrace v1 e ajustes de envelope
**APROVADA**, com a decisão explícita de **alterar também o envelope JSON público LCP Evidence v1**, e não apenas o tipo TypeScript interno:
- `agent.name` aceita `string não vazia | null` tanto no envelope como no modelo interno.
- `event.position` é opcional e pode ser `null`, posição ordinal de geração (`basis: ordinal`, `lane: llm_step`, `ordinal`) ou intervalo de ferramenta em nanossegundos monotônicos (`basis: monotonic_ns`, `lane: span`, `start_ns`, `end_ns`). Valores do relógio monotônico em número JSON devem ser `Number.isSafeInteger`, >=0, e `end_ns >= start_ns`; rejeitar arredondamento.
- `seq` é índice de serialização determinístico, **não afirmação de cronologia entre faixas**; ordenar gerações por `step_number` e spans por `start_ns` e `span_id`; geracões primeiro, spans depois, documentando `PARTIAL_ORDER_ONLY`.
- Somente para `bash`, código de saída inteiro 0 -> success, inteiro diferente de 0 -> error; ausente/null -> unknown. Para ferramentas desconhecidas status unknown. `final_answer` é evento `message` de status unknown, não chamada de ferramenta operacional, mesmo quando vem no array `spans`.
- `telemetry` é descartada (se presente, aviso único `TELEMETRY_IGNORED`); `dataset_name` string|null -> `source.reference`; `_sample_sanitized` é **declaração não verificada**, alerta específico. Conteúdo privado, prompts, tool inputs/outputs e `reasoning_content` jamais propagados ao objeto normalizado.
- Proveniência: `source.kind=trace`, `source.format=agenttrace.lcp-adapter.v1`, `source.producer=pagarsky/agent-trace`, mais aviso `SOURCE_NOT_AUTHENTICATED`.
- Um JSON objeto por arquivo; múltiplas linhas JSONL não são silently ignored; limite 5 MiB/10.000 eventos somando spans+LLMSteps; IDs únicos, números válidos, pais de spans existentes, tipo de span suportado `TOOL`; ausência de informação vira null.
- Ajustes de contrato e testes de regressão anteriores precisam ser feitos **na Etapa B**, explicitamente. Não alterar status do contrato sem registrar a CR-002.

## Evidências de encerramento da Etapa A (reportadas pelo operador)
- SHA local: `a4e4cfebfe086c514bfc0ac08342312297ac3c7e`.
- Vitest focado: **21/21 PASS** (12h26, 14/11/2026, executado pelo operador).
- Frontend regressão: **30/30 PASS** (mesma sessão).
- TypeScript/Vite build: **PASS** (mesma sessão).
- `npm audit --omit=dev`: **0 vulnerabilidades reportadas** (não equivale a auditoria das devDependencies).
- Mefisto: `passed_with_restrictions` antes da aprovação humana da CR-001; nenhuma falha concreta nas correções revisadas. Evidência na mensagem do operador; **não reexecutada pelo revisor**.
- Ainda não foi feita atualização do arquivo local `validation-stage-a.md`, nem uma revisão posterior da implementação alinhada à CR-002. A Etapa A pode ser **encerrada sob CR-001**, desde que o agente local registre aprovação e evidências antes do próximo handoff.

## Autorização para a próxima execução
**Etapa B liberada apenas para edição local de código/fixtures/testes e documentos relacionados ao adaptador.** Operador controla a execução de testes/builds, instalações, downloads, venv, containers, migrações e push/PR que dispare CI. Git, `gh`, shell leve, leitura/edição e commits locais autorizados.

**Etapas C, D, deploy, merge e publicação não estão autorizados por esta decisão.** Nenhuma execução externa de agente ou chamada paga está autorizada.
