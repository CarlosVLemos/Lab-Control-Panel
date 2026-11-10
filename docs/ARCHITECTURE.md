# Arquitetura

Monólito modular com API FastAPI, PostgreSQL para estado/auditoria e worker separado para execuções longas. Adaptadores de workload implementam `prepare → run → collect`; avaliadores são independentes e retornam evidências tipadas. O Policy Engine emite `PASS`, `FAIL`, `INCONCLUSIVE` ou `MANUAL_REVIEW`. Code Gate controla aprovação de mudanças; Release Controller controla canary e rollback.

```text
Vue UI -> Control API -> PostgreSQL
                 | 
                 +-> Redis/RQ -> Worker -> Response / Task / Code
                                            | 
                                            v
                                       Evaluation Engine
                                            |
                                       Policy Engine
                                         /     \
                                   Code Gate   Release Controller
```

**Decisão:** infraestrutura pequena primeiro. Evoluir para OpenTelemetry, Langfuse e Argo somente depois do fluxo ponta a ponta funcionar. O executor de código do MVP não recebe acesso irrestrito a shell/rede.
