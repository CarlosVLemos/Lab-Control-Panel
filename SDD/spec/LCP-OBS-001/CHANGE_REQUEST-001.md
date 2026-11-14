# CR-001 — Delimitação de `summary` por etapa

**Estado:** APPROVED · **Aprovação humana:** 2026-11-14, registrada em `APPROVALS_2026-11-14.md`.
**Afeta:** `contract.md`, seção 3 — Normalização interna.
**Não autoriza:** implementação da Etapa C, agregações, indicadores, Etapa B ou alteração do envelope JSON v1.

## Problema

O contrato FROZEN menciona `summary` na representação interna, mas não define seus campos, fontes, nulidade ou regras de cálculo. A Etapa A foi autorizada somente para modelo, validação e normalização do envelope. Inventar uma estrutura de resumo nesta etapa anteciparia as agregações reservadas à Etapa C.

## Alteração proposta

Substituir a primeira frase da seção 3 por:

> Na Etapa A, a representação normalizada somente leitura contém `runId`, `sourceKind`, `events[]` e `warnings[]`, além dos demais campos declarativos preservados pelo parser. `summary` é responsabilidade da Etapa C e não integra o resultado obrigatório do parser da Etapa A. Sua estrutura e regras de cálculo devem ser congeladas antes da implementação da Etapa C.

## Impacto

- Nenhuma alteração no envelope público `lcp.observation.v1`.
- Nenhuma alteração necessária na API `parseLcpObservation` da Etapa A.
- Nenhuma métrica, soma, estimativa ou indicador é antecipado.
- A Etapa C continua sujeita a gate e contrato próprios.

## Gate

Aprovada para integrar o contrato FROZEN: `summary` não faz parte das Etapas A ou B. Sua forma obrigatória permanece sujeita a contrato, testes e gate próprios antes da Etapa C.
