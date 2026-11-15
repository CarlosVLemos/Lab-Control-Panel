# Kubernetes local (kind)

Laboratório do Lab Control Panel com a mesma divisão do Docker Compose: FastAPI, frontend Vue/Vite e PostgreSQL. Não é um ambiente de produção.

## Recursos

- `Deployment` e `Service` para API e frontend.
- `StatefulSet`, `Service` headless e PVC de 1 GiB para PostgreSQL.
- `Job` separado e idempotente para `alembic upgrade head`.
- Startup/liveness da API independentes do banco e readiness que exige PostgreSQL na revisão Alembic esperada.
- Requests/limits, tokens de ServiceAccount desabilitados e containers sem elevação de privilégios.
- `Secret` criado pelo operador, fora do Git, e imagens carregadas diretamente no kind.
- Kustomize nativo do `kubectl`, sem Helm ou controladores externos.

## Pré-requisitos

- Linux com Docker em execução e acesso do usuário ao daemon.
- `kind` e `kubectl` compatíveis com uma versão de Kubernetes suportada por ambos.
- Bash para a leitura segura da senha.
- `curl` e `cmp` para a validação funcional.
- Acesso à internet, ou cache local equivalente, para imagens base e dependências de `pip`/`npm`.
- Portas locais 5173 e 8000 livres durante os port-forwards.

Registre `docker version`, `kind version` e `kubectl version --client` junto à evidência da execução.

## Criar o cluster e as imagens

Na raiz do repositório:

```sh
kind create cluster --name lcp

docker pull postgres:16
docker build -f backend/Dockerfile -t lcp-api:kind-v1 .
docker build -f frontend/Dockerfile -t lcp-frontend:kind-v1 frontend/
kind load docker-image postgres:16 lcp-api:kind-v1 lcp-frontend:kind-v1 --name lcp

kubectl --context kind-lcp apply -f k8s/kind/namespace.yaml
```

Crie uma senha não vazia sem colocá-la no histórico ou nos argumentos de um processo. O valor percorre stdin e o trecho chama Bash mesmo quando o terminal do operador é Fish:

```sh
bash -c '
set -euo pipefail
read -rsp "Senha local do PostgreSQL: " DB_PASS
printf "\n"
if [[ -z "$DB_PASS" ]]; then
  printf "A senha não pode ser vazia.\n" >&2
  exit 1
fi
printf "%s" "$DB_PASS" |
  kubectl --context kind-lcp -n lcp create secret generic lcp-postgres \
    --from-file=password=/dev/stdin --dry-run=client -o yaml |
  kubectl --context kind-lcp apply -f -
unset DB_PASS
'
```

Se o PVC `postgres-data-postgres-0` já existir, reutilize a senha original. `POSTGRES_PASSWORD` só inicializa um diretório de dados vazio; atualizar apenas a Secret não altera a senha armazenada no banco. Veja **Rotação da senha** antes de usar um valor novo.

## Aplicar e validar

Inicie o PostgreSQL primeiro. Em seguida, aplique o conjunto completo; a API só fica Ready depois que o Job registrar a revisão Alembic `0001`:

```sh
kubectl --context kind-lcp -n lcp apply -f k8s/kind/postgres.yaml
kubectl --context kind-lcp -n lcp rollout status statefulset/postgres --timeout=180s

kubectl --context kind-lcp apply -k k8s/kind
kubectl --context kind-lcp -n lcp wait --for=condition=complete job/lcp-migrate --timeout=620s
kubectl --context kind-lcp -n lcp logs job/lcp-migrate
kubectl --context kind-lcp -n lcp rollout status deployment/api --timeout=180s
kubectl --context kind-lcp -n lcp rollout status deployment/frontend --timeout=180s

kubectl --context kind-lcp -n lcp get pods,services,jobs,pvc
kubectl --context kind-lcp -n lcp exec postgres-0 -- \
  psql -U lcp -d lcp -Atc "SELECT version_num FROM alembic_version"
```

O último comando deve imprimir `0001`. Confirme a comunicação frontend → Service da API dentro do cluster:

```sh
kubectl --context kind-lcp -n lcp exec deployment/frontend -- \
  node -e "fetch('http://api:8000/health').then(r => { if (!r.ok) process.exit(1); return r.text() }).then(console.log).catch(() => process.exit(1))"
```

Exponha o frontend apenas na máquina local:

```sh
kubectl --context kind-lcp -n lcp port-forward service/frontend 5173:5173
```

Abra **http://localhost:5173**. Em *Experimentos → Classificação sintética*, clique em *Executar comparação*. A aplicação deve registrar seis casos no banco.

Para validar a API, mantenha este port-forward em outro terminal:

```sh
kubectl --context kind-lcp -n lcp port-forward service/api 8000:8000
```

E execute:

```sh
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ready
curl -fsS -X POST http://127.0.0.1:8000/api/demo/experiments
curl -fsS http://127.0.0.1:8000/api/demo/experiments/demo-support-intents-v1
```

`/health` verifica somente o processo HTTP. `/ready` conecta ao PostgreSQL e exige a revisão Alembic configurada no Deployment.

## Persistência após reinício do Pod

Com o port-forward da API ativo:

```sh
curl -fsS http://127.0.0.1:8000/api/demo/experiments/demo-support-intents-v1 > /tmp/lcp-before.json
kubectl --context kind-lcp -n lcp delete pod postgres-0
kubectl --context kind-lcp -n lcp wait --for=condition=Ready pod/postgres-0 --timeout=180s
curl -fsS http://127.0.0.1:8000/ready
curl -fsS http://127.0.0.1:8000/api/demo/experiments/demo-support-intents-v1 > /tmp/lcp-after.json
cmp /tmp/lcp-before.json /tmp/lcp-after.json
```

`cmp` deve terminar com status zero. Não remova o PVC durante o teste; excluir o cluster kind também elimina o armazenamento local do laboratório.

## Diagnóstico e recuperação da migração

Se o Job atingir `backoffLimit` ou `activeDeadlineSeconds`, inspecione antes de recriá-lo:

```sh
kubectl --context kind-lcp -n lcp get job/lcp-migrate -o wide
kubectl --context kind-lcp -n lcp get pods -l app=lcp-migrate -o wide
kubectl --context kind-lcp -n lcp describe job/lcp-migrate
kubectl --context kind-lcp -n lcp logs -l job-name=lcp-migrate \
  --all-containers=true --prefix=true --max-log-requests=10
kubectl --context kind-lcp -n lcp get events --sort-by=.lastTimestamp
```

Depois de corrigir a causa — PostgreSQL indisponível, Secret incorreta ou imagem ausente — recrie o Job de forma controlada:

```sh
kubectl --context kind-lcp -n lcp delete job lcp-migrate
kubectl --context kind-lcp apply -k k8s/kind
kubectl --context kind-lcp -n lcp wait --for=condition=complete job/lcp-migrate --timeout=620s
kubectl --context kind-lcp -n lcp logs job/lcp-migrate
```

Excluir primeiro também é necessário quando `spec.template` ou a imagem do Job mudar, pois esse campo é imutável. `alembic upgrade head` pode ser repetido: uma execução bem-sucedida na revisão atual não reaplica a migração.

## Rotação da senha

Não troque apenas a Secret quando o PVC já contém um banco. Em uma janela de manutenção do laboratório, altere primeiro a credencial no PostgreSQL por uma sessão interativa:

```sh
kubectl --context kind-lcp -n lcp exec -it postgres-0 -- \
  psql -U lcp -d lcp -c '\password lcp'
```

Informe o mesmo valor novo no bloco seguro de criação da Secret apresentado anteriormente. Depois reinicie os consumidores para que recebam a variável atualizada:

```sh
kubectl --context kind-lcp -n lcp rollout restart statefulset/postgres
kubectl --context kind-lcp -n lcp rollout restart deployment/api
kubectl --context kind-lcp -n lcp rollout status statefulset/postgres --timeout=180s
kubectl --context kind-lcp -n lcp rollout status deployment/api --timeout=180s
curl -fsS http://127.0.0.1:8000/ready
```

Se a rotação for interrompida entre a alteração no banco e a atualização da Secret, conclua os passos com a nova senha; não apague o PVC como mecanismo de recuperação.

## Limites conhecidos

- O frontend usa o servidor de desenvolvimento Vite e ainda inicia como root. O manifesto remove capabilities e impede elevação de privilégios, mas não elimina esse risco.
- O PostgreSQL executa como UID/GID `999`, usado pelo usuário `postgres` da imagem Debian oficial `postgres:16`; `fsGroup` concede acesso ao PVC sem bootstrap root. Essa compatibilidade precisa ser confirmada no cluster do operador antes de tratar a implantação como validada.
- A readiness abre uma conexão curta a cada verificação. Ela comprova conectividade e revisão Alembic, não integridade completa de todas as tabelas.
- O Job `lcp-migrate` é de execução única e upgrades exigem exclusão/recriação controlada ou um novo nome versionado. O manifesto não automatiza upgrades.
- As tags `postgres:16`, `lcp-api:kind-v1` e `lcp-frontend:kind-v1` são mutáveis e destinadas ao laboratório. Ao alterar código ou migrações, use novas tags, carregue as imagens e atualize os manifests.
- Não há Ingress, TLS público, HPA, backup, RBAC de aplicação, observabilidade, política de rede ou alta disponibilidade. O armazenamento depende do provisionador local do kind; não exponha o banco ou a aplicação à internet.
- `kubectl kustomize k8s/kind` verifica apenas renderização. Somente a execução dos passos acima produz evidência operacional, e ainda não certifica prontidão para produção.
