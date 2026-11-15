# Kubernetes local (kind)

Configuração de laboratório do Lab Control Panel. Mantém a mesma divisão do Docker Compose: FastAPI, frontend Vue/Vite e PostgreSQL. Não é um ambiente de produção.

## Recursos

- `Deployment` e `Service` para API e frontend.
- `StatefulSet`, `Service` headless e `volumeClaimTemplates` de 1 GiB para PostgreSQL.
- `Job` separado para `alembic upgrade head`.
- Probes de startup, readiness e liveness, requests/limits e usuário não-root na API e na migração.
- `Secret` criado pelo operador, fora do Git. As imagens da aplicação são carregadas diretamente no cluster kind.
- `Kustomize` nativo do `kubectl`; sem Helm ou controladores externos.

## Executar

Requisitos: Docker, [kind](https://kind.sigs.k8s.io/docs/user/quick-start/) e kubectl. Na raiz do repositório:

```sh
kind create cluster --name lcp

docker build -f backend/Dockerfile -t lcp-api:kind-v1 .
docker build -f frontend/Dockerfile -t lcp-frontend:kind-v1 frontend/
kind load docker-image lcp-api:kind-v1 lcp-frontend:kind-v1 --name lcp

kubectl --context kind-lcp apply -f k8s/kind/namespace.yaml
```

Crie a senha no namespace sem incluí-la no comando salvo no histórico do shell. O trecho abaixo chama Bash, mesmo em um terminal Fish:

```sh
bash -c 'read -rsp "Senha local do PostgreSQL: " DB_PASS; echo; kubectl --context kind-lcp -n lcp create secret generic lcp-postgres --from-literal=password="$DB_PASS" --dry-run=client -o yaml | kubectl --context kind-lcp apply -f -'
```

Aplique os manifests e aguarde as verificações:

```sh
kubectl --context kind-lcp apply -k k8s/kind
kubectl --context kind-lcp -n lcp rollout status statefulset/postgres --timeout=180s
kubectl --context kind-lcp -n lcp wait --for=condition=complete job/lcp-migrate --timeout=180s
kubectl --context kind-lcp -n lcp rollout status deployment/api --timeout=180s
kubectl --context kind-lcp -n lcp rollout status deployment/frontend --timeout=180s

kubectl --context kind-lcp -n lcp get pods,services,jobs,pvc
kubectl --context kind-lcp -n lcp port-forward service/frontend 5173:5173
```

Abra **http://localhost:5173**. Em *Experimentos → Classificação sintética*, clique em *Executar comparação*. A aplicação deve registrar seis casos no banco.

Para inspecionar a API em outro terminal:

```sh
kubectl --context kind-lcp -n lcp port-forward service/api 8000:8000
```

Com o port-forward acima ativo, em outro terminal:

```sh
curl -fsS http://127.0.0.1:8000/health
curl -fsS -X POST http://127.0.0.1:8000/api/demo/experiments
curl -fsS http://127.0.0.1:8000/api/demo/experiments/demo-support-intents-v1
```

O `GET` deve recuperar o experimento salvo. Para verificar persistência, registre a resposta, reinicie apenas o Pod `postgres-0`, aguarde o StatefulSet e compare o `GET` novamente. **Não remova o PVC** durante esse teste.

## Limites conhecidos

- O frontend executa o **servidor de desenvolvimento Vite** da imagem atual, não um servidor estático endurecido. A imagem ainda inicia como root; o manifesto remove capabilities e impede elevação de privilégios, mas não elimina esse risco.
- `/health` na API verifica o processo HTTP, **não** o estado da conexão PostgreSQL. Aguarde o Job de migração antes do teste funcional.
- O Job `lcp-migrate` é de execução única. Em uma nova versão do banco, use um novo Job ou elimine/recrie o Job anterior de forma controlada antes de expor a nova API. O manifesto não automatiza upgrades.
- `lcp-api:kind-v1` e `lcp-frontend:kind-v1` são tags de laboratório. Ao alterar o código, crie novas tags, carregue as imagens e atualize os manifests; não presuma que imagens locais são atualizadas automaticamente.
- Nenhum Ingress, TLS público, HPA, backup, RBAC de aplicação, observabilidade do cluster, política de rede ou alta disponibilidade foi configurado. O armazenamento depende do provisionador local do kind. Não exponha o banco ou a aplicação à internet.
- A configuração ainda precisa de validação operacional no cluster do operador. `kubectl kustomize k8s/kind` valida a renderização básica; as verificações de runtime acima demonstram a execução, não certificam prontidão para produção.
