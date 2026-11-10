# ADR-003 — Execução controlada e limites de confiança

**Status:** Accepted · **Escopo:** MVP

## Contexto

Um agente pode produzir comandos e patches inseguros. Um container comum não constitui, por si só, sandbox adequada para executar código hostil de terceiros.

## Decisão

- O MVP aceita apenas repositórios fixture controlados e ferramentas/comandos em allowlist.
- Não disponibilizar credenciais, socket Docker ou shell do host para o agente.
- Separar runner de código da API e restringir rede, privilégios, recursos e tempo.
- Capturar comandos, saídas, exit codes, diffs e testes de maneira sanitizada.
- Postergar código externo arbitrário até existir threat model e isolamento reforçado.

## Consequências

Reduz superfície de ataque e permite uma demo reproduzível. O LCP V0.1 não promete executar PRs desconhecidos de forma segura. A execução concreta e testes de isolamento pertencem a LCP-011 e LCP-023.
