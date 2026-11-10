# Criar repositório e GitHub Project

O conector GitHub desta conversa não oferece criação de repositórios nem Projects. Este bootstrap executa essas operações **na sua sessão local autenticada**.

## Pré-requisitos (CachyOS / Arch)

```bash
sudo pacman -S --needed github-cli git python
```

Configure a identidade Git se necessário:

```bash
git config --global user.name "Seu nome"
git config --global user.email "seu-email-do-github"
```

Autentique e autorize GitHub Projects:

```bash
gh auth login
gh auth refresh -s project
```

Da raiz do pacote extraído, execute:

```bash
python3 scripts/bootstrap_github.py --dry-run  # somente lista os itens
python3 scripts/bootstrap_github.py            # cria tudo na sua conta
```

Por padrão, o repositório e o Project serão **públicos** por serem de portfólio. Para criar **repositório e Project privados**, use `python3 scripts/bootstrap_github.py --private` na primeira execução.

O comando cria:

- Repositório `CarlosVLemos/Lab-Control-Panel`, com README curto, API de saúde e CI básica.
- GitHub Project `Lab Control Panel`, vinculado ao repositório, com view Kanban (board).
- Status: Backlog, Ready, In Progress, Review e Done.
- Campos Priority e Phase.
- 25 Issues com dependências, critérios de aceite, labels e milestones.

O script verifica repositório e Issues existentes para evitar duplicação. Em caso de erro, leia a mensagem antes de repetir. Não apague um projeto existente por conta própria.

Links esperados após a criação:

- `https://github.com/CarlosVLemos/Lab-Control-Panel`
- `https://github.com/users/CarlosVLemos/projects/<número do Project>`

**Verificação:** `gh repo view CarlosVLemos/Lab-Control-Panel --web` e `gh project list --owner CarlosVLemos`.
