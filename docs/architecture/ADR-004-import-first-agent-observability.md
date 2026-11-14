# ADR-004 — Observabilidade agêntica por importação de evidências

**Data:** 2026-11-14 · **Decisão de produto:** aceita · **Contrato técnico de implementação:** DRAFT (não FROZEN).

## Contexto e escopo
O LCP já possui frontend Vue, API FastAPI/PostgreSQL para demonstração Response sintética, importador offline CODE-001 e fundação RAG. Ainda não oferece observabilidade de execuções reais externas. O objetivo de portfólio é provar uma fatia funcional hoje, não construir um provedor ou orquestrador de agentes.

## Decisões
1. **Import-first:** a primeira entrega importa um arquivo externo local e mostra uma execução agêntica observável. A fonte pode ter sido um agente local, via API ou de ferramenta de programação; nenhum provedor obrigatório.
2. **Não é executor nem juiz:** o produto não executa agentes, comandos importados ou código de terceiros. Nenhuma IA avalia outra IA. Testes externos podem ser exibidos como evidência, mas não criam nota de qualidade universal.
3. **Frontend-first:** parse, normalização, cálculo e visualização acontecem no navegador, sem upload ou armazenamento de traces no servidor. Reutilizar Vue/Vite e componentes existentes; backend e esquema PostgreSQL não mudam neste marco.
4. **Entradas limitadas e testáveis:** formato declarativo próprio `lcp.observation.v1` e um único formato externo de trace (candidato AgentTrace), selecionado depois de inspecionar uma amostra real fornecida pelo operador. Nenhum suporte genérico a "qualquer JSONL" ou OTLP completo.
5. **Proveniência:** trace observado/reproduzível, autorrelato retrospectivo e fixture gerada são categorias distintas. Não apresentar relato do próprio agente como medição independente.
6. **Sem dados inventados:** valores ausentes são `null` ou "não informado", não zero. Tokens de uma chamada são atribuídos ao instante em que a evidência informa seu consumo; não interpolar consumo por segundo. Não somar tempos de spans aninhados como duração total.
7. **Replay de eventos, não de mouse:** selecionar, avançar, retroceder e reproduzir eventos na timeline com contexto e detalhes. Sem movimentos físicos de cursores, gravação de tela, streaming ou múltiplos mouses no MVP.
8. **Limites operacionais de Codex:** é permitido inspecionar arquivos, usar shell/Git/GitHub CLI e escrever código/documentos quando a etapa for autorizada. Não criar venv, instalar/baixar dependências, modelos ou navegadores, nem executar testes/builds/Compose/containers sem autorização explícita por comando ou lote. O operador provê ambiente e roda testes ao final de cada etapa.

## Consequências e riscos assumidos
- Sem persistência compartilhada nem live tracing; em troca, importação local segura e simples para portfólio.
- Um formato externo concreto evita normalização especulativa; outros adaptadores são extensões futuras.
- A visualização mostra a atividade observada e as lacunas de dados, não fornece recomendações universais sobre eficiência ou boas práticas.
- Para publicar, o build estático da UI poderá ser servido sem expor o backend de importação; deploy público/segurança de produção é etapa separada.

**Fonte normativa do próximo marco:** [Spec](../../SDD/spec/LCP-OBS-001/spec.md) · [Contrato](../../SDD/spec/LCP-OBS-001/contract.md) · [Etapas](../../SDD/spec/LCP-OBS-001/tasks.md) · [Testes](../../SDD/spec/LCP-OBS-001/tests.md).
