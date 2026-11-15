# Kubernetes local — frontend estatico

Deploy do frontend Vue 3 do Lab Control Panel em um cluster kind. Usa Kustomize, Deployment e Service; nao precisa de API, PostgreSQL nem Job Alembic. Os componentes backend e Compose do repositorio continuam disponiveis, mas nao participam deste deploy.

## Testar

Requer Docker, kubectl e kind. A imagem gera o build Vite com `VITE_DEMO_OFFLINE=true`: SWE-bench, CODE-001 e Observabilidade utilizam evidencias locais/importadas; a Classificacao sintetica usa uma **fixture offline**, que nao e a execucao persistida da API. Nao atribua os resultados offline a uma execucao de backend.

Na raiz do repositorio:

```sh
# Confirme o cluster existente; este procedimento nao o recria:
kind get clusters
kubectl --context kind-lcp cluster-info

# Build da UI estatica; nao usa o Dockerfile do Compose. A imagem de build usa
# Node 22 sobre Debian slim para evitar a falha interna do npm observada no Alpine:
docker build --pull --progress=plain --platform linux/amd64 \
  -f frontend/Dockerfile.k8s \
  -t lcp-frontend:kind-static-v1 \
  frontend/

# Compatibilidade com Docker usando image store containerd:
docker image inspect lcp-frontend:kind-static-v1 >/dev/null
docker image save --platform linux/amd64 -o /tmp/lcp-frontend-kind.tar lcp-frontend:kind-static-v1
test -s /tmp/lcp-frontend-kind.tar
kind load image-archive /tmp/lcp-frontend-kind.tar --name lcp

kubectl --context kind-lcp apply -k k8s/kind
kubectl --context kind-lcp -n lcp rollout restart deployment/frontend
kubectl --context kind-lcp -n lcp rollout status deployment/frontend --timeout=180s
kubectl --context kind-lcp -n lcp get deployment,service,pods
kubectl --context kind-lcp -n lcp port-forward service/frontend 8080:8080
```

Com o port-forward ativo, em outro terminal, valide o documento, o fallback de SPA e o isolamento da API:

```sh
curl -fsS http://127.0.0.1:8080/ >/dev/null
curl -fsS http://127.0.0.1:8080/rota-spa-inexistente >/dev/null
test "$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/api/health)" = 404
```

Abra http://localhost:8080. Confirme SWE-bench, CODE-001, Observabilidade/AgentTrace e a classificacao sintetica explicitamente marcada como `Fixture offline`.

## Verificacoes e limites

```sh
kubectl kustomize k8s/kind
kubectl --context kind-lcp -n lcp get pods
kubectl --context kind-lcp -n lcp describe deployment frontend
kubectl --context kind-lcp -n lcp logs deployment/frontend
```

A implantacao e um laboratorio de um no, nao um ambiente de producao. Nao inclui TLS/Ingress publico, autoscaling ou backend. A imagem tem tag local fixa: para atualiza-la, gere uma nova tag, carregue-a no kind e atualize o manifesto. A rota `/api/` retorna 404 intencionalmente, pois nao ha API nesta implantacao.

Em um cluster que ja recebeu os manifests antigos, `kubectl apply -k` **nao apaga** PostgreSQL, API ou Jobs anteriores. Esses recursos antigos precisam ser avaliados e eventualmente removidos pelo operador; um PVC existente deve ser preservado ate que haja decisao explicita sobre seus dados. Nao execute `kubectl delete -k` no cluster antigo para limpar tudo.
