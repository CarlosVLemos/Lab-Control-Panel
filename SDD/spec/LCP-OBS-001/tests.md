# LCP-OBS-001 — Matriz de validação (PLANNED / NOT_RUN)

**Execução:** responsabilidade do operador, ao fim de cada etapa. O Codex prepara testes e relata comandos sugeridos; **não os executa sem autorização explícita**. Nenhuma célula desta matriz constitui teste já executado.

| ID | Etapa | Dado/caso | Critério esperado |
| --- | --- | --- | --- |
| C01 | A | Envelope v1 completo | Parse determinístico; eventos com ordem estável |
| C02 | A | Sem timestamps, modelo, tokens, custo | Importação parcial; campos desconhecidos são null |
| C03 | A | JSON inválido, >5 MiB, >10k eventos, números negativos ou IDs duplicados | Rejeição explícita, sem cálculo parcial enganoso |
| C04 | A | Conteúdo com "ignore instruções" e tags HTML | Tratado como dado, texto escapado; zero execução |
| C05 | A | Autorrelato retrospectivo | Sinaliza SELF_REPORT e não "observado independente" |
| E01 | B | Amostra externa com spans e ferramentas | Mapeamento reproduzível; IDs, tipos e status corretos |
| E02 | B | Formato externo sem uso/erro/timestamps | Mantém desconhecido; sem extrapolação |
| E03 | B | Campo incompatível/versão não suportada | Falha clara ou parcial explicitamente rotulada |
| M01 | C | Duas chamadas com uso incremental | Soma por operação; série em degraus nos eventos medidos |
| M02 | C | Totais cumulativos e spans pai/filho | Sem dupla contagem; ambiguidade exposta |
| M03 | C | Eventos sem tempo, sobrepostos, falha sem duração | Não somar durations para criar tempo total; estados corretos |
| M04 | C | Custo ausente ou modelo/tarifa não confirmados | Null; nunca custo artificial 0 USD |
| U01 | D | Trace externo importado | KPIs, timeline, gráfico e detalhe conferem com dados brutos |
| U02 | D | Play/Pause/Anterior/Próximo e seleção | Estado coerente; sem eventos ou tempos simulados |
| U03 | D | Sem consumo ou trace parcial | Gráfico vazio informativo e lacunas visíveis |
| U04 | D | Dados hostis renderizados na UI | Sem execução de JS/HTML, sem envio ao backend |
| R01 | D/E | Response + Code Evaluation já existentes | Fluxos continuam acessíveis e comportamentos preservados |
| R02 | E | Recurso estático em produção | Nenhum arquivo importado enviado à rede; exposição de API não necessária |

## Gates operacionais
- **Gate A:** operador roda testes focados de contrato.
- **Gate B:** operador roda testes focados de adaptador usando amostra fornecida.
- **Gate C:** operador roda testes focados de métricas.
- **Gate D:** operador roda suíte frontend, build e verificação visual; depois regressão E2E existente se ambiente já estiver preparado.
- **Gate E:** operador revisa diffs, evidências, CI autorizada e decisão de merge/deploy.

Os comandos exatos serão definidos junto aos testes implementados; **não lançar instalações/downloads para consegui-los**. Se a máquina não possui uma dependência, marcar `BLOCKED` e instruir o operador sobre o requisito.

Formato mínimo de evidência por teste: `test_id`, `command`, `environment`, `exit_status`, `result` (PASS/FAIL/NOT_RUN/BLOCKED), `notes`, `commit_sha`. Não inferir PASS a partir de uma expectativa.
