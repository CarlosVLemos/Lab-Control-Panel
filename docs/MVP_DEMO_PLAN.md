# Lab Control Panel — MVP demonstrável para portfólio

**Diretriz:** construir algo pequeno que **funciona**. A visão completa em `docs/PROJECT_SPEC.md` é roadmap; não é pré-requisito para a primeira demo.

## A história que a demo deve contar

Abrir interface Vue 3/TypeScript/Vite, selecionar um dataset sintético versionado e executar **baseline vs candidato** usando adaptadores Response mock determinísticos. Mostrar taxa de acerto, erros por caso, tempo de execução medido pela API, evidências e vereditos. Tokens/preço simulados devem ser rotulados `mock`, nunca apresentados como medição real. Os dados sobrevivem ao reinício em PostgreSQL.

## Ordem do trabalho

1. **#2 LCP-002:** PostgreSQL + Alembic + SQLAlchemy + Compose/CI, mínimo e estável.
2. **#4/#5:** dataset de fixture e versões de candidatos.
3. **#6/#7/#9:** executor Response mock e comparação determinística entre baseline e candidato, com endpoint simples para demo.
4. **#15:** uma página Vue de comparação, evidências, loading/erro/empty; sem dashboard gigante.
5. **#16/#17:** fluxo E2E, Compose com API/web/DB, builds, diagrama de arquitetura, vídeo de 2–3 minutos e README curto.
6. **Kubernetes local como demonstração DevOps (recorte de #16):** após funcionar com Docker, usar `kind` + Kustomize com Deployment/Service, readiness/liveness, CPU/memory requests e limites apropriados, non-root, sem escalation/ServiceAccount token; ConfigMap + referência a Secret **sem valor real versionado**. Testar aplicação de manifests e smoke test no cluster antes de reivindicar uso de K8s.

## Boas práticas demonstráveis

- Dockerfile enxuto e não-root, .dockerignore, healthchecks e volume PostgreSQL. Multi-stage somente quando reduzir imagem/complexidade.
- pytest real com DB, GitHub Actions para API/frontend e build de imagens; imagens GHCR opcionais após CI, sem secrets em logs.
- Swagger/OpenAPI, tipagem e erros coerentes, migrations versionadas, tratamento de erros, Git/PRs e evidências verificáveis.
- Manifestos Kubernetes com `kubectl kustomize`, probes e securityContext; **não** instalar Helm/Argo/Rollouts só para mencionar no currículo.
- Limitações claras: mock ≠ LLM real, execução de Code/Task e canary real ficam para depois, Kubernetes local ≠ cluster de produção.

## Não fazer no MVP de apresentação

Redis/RQ sem necessidade, runner de código de terceiros, políticas complexas, multi-tenant, Argo Rollouts, OpenTelemetry completo, LLM-as-judge, deploy automatizado de produção ou 20 telas. Priorizar fatia vertical completa.

**Definition of Done:** o demo executa comparação, exibe resultado, persiste dados, sobe pelo Compose, tem CI reproduzível e captura para portfólio. Kubernetes é incluído na apresentação **somente após execução comprovada** em kind.

Referências: https://docs.docker.com/build/building/best-practices/ ; https://kubernetes.io/docs/concepts/security/application-security-checklist/ ; https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/ .
