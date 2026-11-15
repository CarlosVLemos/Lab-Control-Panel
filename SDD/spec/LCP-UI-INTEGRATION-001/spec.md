# LCP-UI-INTEGRATION-001 — Reconciliar limpeza da UI com a main

**Estado:** DRAFT — reconciliação e validação pendentes.
**Trilha:** STANDARD (ajustes de interface e testes; sem mudança de contratos de API, banco ou execução).
**Origem:** PR #48 (`chore/ui-copy-cleanup-20261114`).
**Decisão do operador (15/11/2026):** a limpeza de textos promocionais e redundâncias da interface é necessária e deve ser preservada; não descartar seu objetivo por conflito de Git.
**Alvo:** `main` atualizada após os merges #41, #50, #54 e #55.

## Objetivo

Entregar uma UI direta, sem slogans, badges e comentários repetitivos, preservando funcionalidade e proveniência de evidências. A integração não deve reverter alterações recentes de SWE-bench, CODE-001, classificação sintética ou Observabilidade/AgentTrace.

## Diagnóstico verificado em 15/11/2026

- A PR #48 possui CI verde no SHA `a8b3993982f4983b8573e2b011f69d42b43a9679`, mas apresenta conflitos com a `main`; a comparação indicava 4 commits à frente e 43 atrás na ocasião.
- A `main` já contém **boa parte — possivelmente a totalidade funcional — da limpeza**: o `App.vue` atual não contém os slogans, botões de erro demonstrativo ou badges promocionais removidos pela #48; `CodeEvaluationView.vue` na `main` corresponde à versão limpa da #48; os testes E2E atuais verificam ausência dos slogans, rodapé e banners em várias telas.
- A versão da #48 tem uma navegação antiga de duas views, enquanto a `main` já inclui SWE-bench e Observabilidade; copiar `App.vue`, `styles.css` ou `demo.spec.ts` inteiros da #48 causaria regressões.
- **CI verde na branch antiga não comprova equivalência com a `main` atual.** Não interpretar conflito de Git como falta da funcionalidade.
- O diff residual e a equivalência visual/funcional exigem validação antes de decidir merge ou encerramento por conteúdo já incorporado.

## Escopo

**Inclui:** auditoria semântica da PR #48 contra `main`; remoção apenas de redundâncias ainda presentes; integração de testes de regressão de copy e UX; registro das evidências e decisão final sobre a PR.

**Fora de escopo:** redesenho amplo, novos experimentos, mudança de dados/fixtures ou de seus hashes, APIs, migrations, Kubernetes, execução de agentes, alteração de métricas e remoção de avisos técnicos necessários.

## Invariantes obrigatórias

1. A navegação mantém **Experimentos → SWE-bench / CODE-001 / Classificação sintética** e **Observabilidade**.
2. SWE-bench permanece identificado como **evidência importada**, não execução local.
3. CODE-001 mantém `COMPARÁVEL` / `INCONCLUSIVA`, `SEM VENCEDOR` e métricas desconhecidas quando não registradas.
4. Classificação sintética explicita fonte `API` ou `Fixture offline` conforme o build; falha de backend deve continuar visível, sem fallback silencioso.
5. AgentTrace e evidências locais continuam importadas e processadas no navegador, com estados de erro, lacunas e proveniência preservados.
6. Remover slogans/decoração não significa ocultar a natureza sintética, dados ausentes, erros de importação ou limitações do experimento.
7. Nenhuma mudança no backend/DB ou nos manifests de deploy para resolver conflitos de apresentação.

## Plano de implementação — Van Gogh

1. Ler `AGENTS.md`, `SDD/rules.md`, esta Spec, diff completo da #48 e os arquivos atuais da `main`.
2. Comparar **comportamento e conteúdo**, não apenas hashes ou linhas. Produzir matriz por alteração da #48: `já está na main` / `falta` / `não deve voltar`, com referência ao código.
3. Se tudo estiver na `main`, **não forçar merge** de código obsoleto. Recomendar o encerramento da #48 como `superseded / already integrated`, com evidências; obter decisão do operador antes de fechar.
4. Se houver diferenças desejadas, aplicar apenas as faltantes **sobre a `main` atual**. Não substituir componentes ou CSS atuais por versões antigas. Resolver os conflitos no fluxo de branch autorizado, sem `push --force`, e preservar histórico.
5. Atualizar testes Playwright somente quando necessários para refletir navegação real e provar a limpeza. Não transformar testes de fonte API em testes da fixture offline.
6. Executar avaliação independente (Mefisto) sobre diff final e riscos de regressão quando autorizada. Registrar `PASS` / `FAIL` / `NOT_RUN` por verificação.
7. Só solicitar merge da PR #48 se houver alterações efetivamente ausentes na `main`, CI verde **na versão integrada** e aprovação humana. Caso contrário, justificar que a funcionalidade já existe na `main`.

## Critérios de aceitação

- `App.vue` preserva todas as áreas atuais; nenhum texto promocional ou rodapé redundante é reintroduzido.
- `CodeEvaluationView.vue` continua mostrando resultados e limites com copy concisa.
- API/fixture e importações externas mantêm indicação inequívoca de fonte.
- Falhas não desaparecem; estados vazios/inválidos continuam observáveis.
- Testes de regressão referentes às quatro áreas são compatíveis com os nomes atuais da navegação.
- Nenhuma exclusão de funcionalidade, regressão de CSS ou reintrodução de copy antiga.
- Há uma decisão fundamentada para #48: **merge de delta real** ou **encerramento por equivalência comprovada**, sem merge simbólico.

## Verificações — autorização do operador necessária para execução

```sh
git diff --check
cd frontend
npm test
npm run build
# Playwright com ambiente E2E e serviços necessários, segundo a configuração atual:
npx playwright test --config playwright.config.ts
```

Inspecionar especificamente: classificação sintética por API, modo offline do Kubernetes, CODE-001, SWE-bench e Observabilidade/AgentTrace. Comparar capturas visuais antes/depois quando necessário. A CI antiga da #48 não substitui esses testes.

**Estado de execução desta Spec:** `NOT_RUN`. Nenhuma instrução acima autoriza instalações, builds, testes, Docker, pushes adicionais, comentários no GitHub, fechamento da PR ou merge automático.
