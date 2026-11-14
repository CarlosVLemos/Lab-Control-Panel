# LCP-OBS-001 — Especificação funcional da observabilidade agêntica

**Estado:** DRAFT / PLANNED. **NÃO autoriza implementação ainda.**
**Trilha:** CRITICAL (arquivos de terceiros, fronteira de importação + interface pública).
**Base de planejamento:** `main@8d4efebc305b2cf671d807ea42d82873373434ff` em 2026-11-14.
**Decisão:** [ADR-004](../../../docs/architecture/ADR-004-import-first-agent-observability.md).

## 1. Objetivo do produto
O usuário seleciona um trace local de execução agêntica, visualiza a sequência observada de chamadas de modelo/ferramenta e eventos, identifica erros e observa consumo acumulado e tempos **onde houver medição**. O LCP deve permanecer útil quando o trace estiver incompleto, indicando expressamente suas limitações.

**Não objetiva** provar qual modelo é melhor, julgar semântica de respostas com IA, inferir intenção privada do modelo ou quantificar dados que não foram coletados.

## 2. Personas e histórias
- **Desenvolvedor com trace externo:** importar arquivo → validar → ver resumo de execução → navegar na linha do tempo → inspecionar evento, métricas e fonte.
- **Operador com conversa já concluída:** copiar instruções em `LCP_EXPORT.md` → pedir ao agente um manifesto declarativo dos dados realmente acessíveis → importar como **autorrelato**, identificando eventos/consumo ausentes.
- **Pessoa avaliando portfólio:** abrir amostra **sanitizada e marcada** como dataset de terceiros ou fixture e percorrer o replay sem necessidade de chaves/contas locais.

## 3. Escopo fechado para MVP
**Inclui:** (a) normalização do formato LCP Evidence v1; (b) um adaptador de formato externo baseado em amostra real conferida; (c) validação e classificação de métricas; (d) KPIs; (e) gráfico discreto/acumulado de consumo; (f) timeline com eventos, filtros e replay; (g) inspeção de erro/ferramenta e proveniência; (h) estado de arquivo inválido, vazio, parcial e sucesso; (i) prompt de exportação declarativa.

**Exclui:** scraping de conversas via login, live tracing, instrumentação nativa OTel completa, integração com provedores usando chaves, LLM-as-judge, execução de comandos presentes em dados, sandbox de código, worker/Redis/RQ, migração SQL, upload HTTP, autenticação, multiusuário, custo estimado sem preço/tier/modelo verificáveis, replay real de mouse, IA local embutida e dashboards paralelos.

## 4. Regras de domínio
- `trace`, `self_report` e `fixture` são proveniências diferentes. Adição de hash SHA-256 é integridade de bytes, não autenticação da fonte.
- Aceitar tanto `event index` (ordem) como timestamps; quando faltam timestamps, mostrar sequência ordinal, não duração calculada.
- Consumir report de uso de tokens por chamada de modelo apenas quando fonte/semântica forem claras. Não somar total cumulativo com valor incremental; evitar duplicação de span pai/filho.
- Duração da execução requer timestamp inicial/final confiável ou duração declarada; caso contrário mostrar `not available`. Duração de operações sobrepostas não se soma para produzir "tempo total".
- Contagem de ferramentas conta operações identificáveis, não mensagens. Falha explícita não pode ser convertida em sucesso por ausência de erro textual; eventos sem estado ficam desconhecidos.
- Custos em USD são estritamente `reported` ou `estimated` com referência/versão de tarifa. Sem tarifa e conta/tier, `null`; não comparar diferentes modelos só por tokens.
- Um evento tem referência estável para inspeção e eventual fonte/segmento original. Texto do arquivo importado é **dado não confiável**, inclusive trechos com "instruções".
- Quando o arquivo contém somente conversa, nenhum comando, tempo, uso de token ou falha deve ser fabricado.

## 5. UX mínimo
Nova área/tab `Observability` na interface existente, preservando `Response` e `Code Evaluation`. Elementos:
1. Importar arquivo local com limite explícito de tamanho; estados vazio/carregando/inválido/parcial.
2. Resumo: tipo de fonte, agentes/modelos reportados, duração, eventos, chamadas de ferramentas, erros, tokens (input/output), custo opcional, cobertura de observação.
3. Consumo **por etapa registrada**: série em degraus/cumulativa de tokens de LLMStep, sem inferir timestamp de geração. Eixo de tempo só quando os eventos possuem horários comparáveis. Lacunas identificadas; sem consumo, exibir estado vazio.
4. Replay: lista ordenada com reprodução baseada em eventos (Play/Pause/Anterior/Próximo), seleção e detalhe; ferramentas com spans monotônicos podem mostrar duração relativa; LLMSteps sem timestamps são ordinalmente navegáveis, sem inventar intervalos ou alinhamento temporal entre faixas.
5. Detalhe: tipo, identificador, timestamps, status, métricas, fonte, dados truncados/sanitizados; não renderizar HTML/JS de entrada.

## 6. Dados e exemplos
- Fonte externa inicial **selecionada**: AgentTrace (NL2Bash/Qwen3-0.6B); ver [mapeamento e limites](source-agenttrace.md). Uma linha real ainda depende de fornecimento, sanitização e revisão pelo operador. Não afirmar que existe amostra já baixada.
- Exemplo sintético próprio deve ser rotulado `fixture` e jamais descrito como execução real. Criar caso completo, parcial, faltando timestamps, faltando token, tokens cumulativos/incrementais, spans sobrepostos, erros, eventos sem outcome, campo desconhecido, tamanho excedido e JSON malformado.
- Preservar CODE-001 existente como experiência separada. Nenhuma alteração em hashes, fixtures e contratos congelados do RAG para facilitar LCP-OBS-001.

## 7. Riscos
Principal risco: apresentação visual mais precisa do que a fonte permite; segundo: formatos heterogêneos; terceiro: arquivos não confiáveis e dados potencialmente privados; quarto: regressão das telas existentes. Todos precisam de testes de contrato e validação explícita.

## 8. Critérios de conclusão
- Um arquivo **externo real** alimenta a UI sem hardcode dos números.
- Arquivo LCP Evidence v1 retrospectivo pode ser importado, com autorrelato e lacunas visíveis.
- Linha do tempo e gráfico reagem à seleção/replay, e não simulam eventos inexistentes.
- Números conferem com fixtures e amostra de entrada; `null` não vira zero nem status de sucesso.
- Response e Code Evaluation permanecem funcionais; sem alterações no backend/DB.
- Cada etapa tem teste preparado e relatório de execução **do operador**, não do Codex, salvo autorização pontual posterior.
- Handoff e documentação atualizados sem alegar live monitoring, GPU ou integração de provedor.

**Aprovação humana de contrato FROZEN e execução é gate separado; esta Spec ainda está DRAFT.**
