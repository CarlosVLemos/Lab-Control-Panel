#!/usr/bin/env python3
"""Create the Lab Control Panel repository, GitHub Project board and issue backlog.

Requires authenticated GitHub CLI with project scope. Idempotent for matching
repository, board, milestone titles and exact issue titles.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "CarlosVLemos"
REPO = f"{OWNER}/Lab-Control-Panel"
PROJECT_TITLE = "Lab Control Panel"
BACKLOG = json.loads((Path(__file__).parent / "backlog.json").read_text(encoding="utf-8"))


def command(*args: str, check: bool = True, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(list(args), cwd=cwd, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"{' '.join(args[:4])}: {p.stderr.strip() or p.stdout.strip()}")
    return p


def gh(*args: str, check: bool = True) -> str:
    return command("gh", *args, check=check).stdout.strip()


def gh_json(*args: str) -> dict:
    raw = gh(*args)
    data = json.loads(raw)
    if isinstance(data, dict) and data.get("errors"):
        raise RuntimeError(f"GraphQL: {data['errors']}")
    return data


def graphite(query: str, **vars: str) -> dict:
    arguments = ["api", "graphql", "-f", f"query={query}"]
    for key, val in vars.items():
        arguments += ["-f", f"{key}={val}"]
    return gh_json(*arguments)


def ensure_repo(visibility: str) -> None:
    exists = command("gh", "repo", "view", REPO, "--json", "nameWithOwner", check=False).returncode == 0
    if exists:
        print(f"[repo] existente: https://github.com/{REPO} (não sobrescrever)")
        return
    if not (ROOT / ".git").exists():
        command("git", "init", "-b", "main")
    command("git", "add", ".")
    if command("git", "diff", "--cached", "--quiet", check=False).returncode:
        try:
            command("git", "commit", "-m", "chore: initialize Lab Control Panel")
        except RuntimeError as error:
            raise RuntimeError(f"{error}\nConfigure git user.name e user.email antes de executar.") from error
    gh("repo", "create", REPO, f"--{visibility}", "--description",
       "AI evaluation, experiments and release governance", "--source", str(ROOT), "--remote", "origin", "--push")
    print(f"[repo] criado: https://github.com/{REPO}")


def ensure_project(visibility: str) -> tuple[int, str, bool]:
    projects = gh_json("project", "list", "--owner", OWNER, "--format", "json", "--limit", "100").get("projects", [])
    current = next((item for item in projects if item.get("title") == PROJECT_TITLE), None)
    created = current is None
    if created:
        current = gh_json("project", "create", "--owner", OWNER, "--title", PROJECT_TITLE, "--format", "json")
    number = int(current["number"])
    gh("project", "edit", str(number), "--owner", OWNER, "--visibility", "PRIVATE" if visibility == "private" else "PUBLIC",
       "--description", "Evaluation, experiments and controlled AI releases")
    gh("project", "link", str(number), "--owner", OWNER, "--repo", REPO)
    detail = gh_json("project", "view", str(number), "--owner", OWNER, "--format", "json")
    print(f"[project] {'criado' if created else 'existente'}: {detail.get('url','')} (# {number})")
    return number, detail["id"], created


def get_fields(number: int) -> dict:
    data = gh_json("project", "field-list", str(number), "--owner", OWNER, "--format", "json", "--limit", "100")
    return {row["name"]: row for row in data.get("fields", [])}


def ensure_fields(number: int, new_project: bool) -> dict:
    fields = get_fields(number)
    if new_project and "Status" in fields:
        query = '''mutation($fieldId:ID!){updateProjectV2Field(input:{fieldId:$fieldId,singleSelectOptions:[
          {name:"Backlog",color:GRAY,description:"Not scheduled"},
          {name:"Ready",color:BLUE,description:"Ready for implementation"},
          {name:"In Progress",color:YELLOW,description:"Under development"},
          {name:"Review",color:PURPLE,description:"Under review and validation"},
          {name:"Done",color:GREEN,description:"Accepted and completed"}
        ]}){projectV2Field{... on ProjectV2SingleSelectField{id name options{id name}}}}}'''
        graphite(query, fieldId=fields["Status"]["id"])
        print("[project] Status: Backlog / Ready / In Progress / Review / Done")
    for name, options in (("Priority", ["P0", "P1", "P2"]),
                          ("Phase", ["Foundation", "Execution", "Evaluation", "Experiments", "Governance", "UI-DevOps", "Security"])):
        if name not in fields:
            gh("project", "field-create", str(number), "--owner", OWNER, "--name", name,
               "--data-type", "SINGLE_SELECT", "--single-select-options", ",".join(options), "--format", "json")
            print(f"[project] campo {name} criado")
    return get_fields(number)


def ensure_board_view(project_id: str, new_project: bool) -> None:
    if not new_project:
        print("[board] Projeto existente; não criar view duplicada")
        return
    query = '''mutation($projectId:ID!){createProjectV2View(input:{
      projectId:$projectId,name:"Kanban",layout:BOARD_LAYOUT
    }){projectV2View{id name layout}}}'''
    try:
        graphite(query, projectId=project_id)
        print("[board] visualização Kanban (BOARD_LAYOUT) criada")
    except RuntimeError as exc:
        print(f"[board] Atenção: a view não foi criada: {exc}")
        print("[board] Crie uma view 'Board' manualmente no GitHub Projects.")


def ensure_labels() -> None:
    labels = {
        "prio:P0": ("B60205", "Required for MVP"),
        "prio:P1": ("D93F0B", "Post-MVP improvement"),
        "prio:P2": ("0E8A16", "Future scope"),
        "type:task": ("5319E7", "Implementation task"),
        "phase:Foundation": ("D4C5F9", "Architecture and persistence"),
        "phase:Execution": ("C2E0C6", "Execution engines and runners"),
        "phase:Evaluation": ("BFDADC", "Evaluation and tests"),
        "phase:Experiments": ("C5DEF5", "Comparative experiments"),
        "phase:Governance": ("F9D0C4", "Policies and release control"),
        "phase:UI-DevOps": ("BFE5F2", "Dashboard, packaging and CI"),
        "phase:Security": ("F9C3C0", "Threat model and isolation"),
    }
    for label, (color, description) in labels.items():
        gh("label", "create", label, "--repo", REPO, "--color", color,
           "--description", description, "--force")
    print(f"[repo] {len(labels)} labels configuradas")


def ensure_milestones() -> None:
    existing = gh_json("api", f"repos/{REPO}/milestones?state=all&per_page=100")
    # gh_json may return array; normalized below.
    titles = {m["title"] for m in existing}
    for name, desc in (("MVP", "V0.1 — evaluation and rollback demonstration"),
                       ("Next", "V0.2 — integrations and extended evaluation"),
                       ("Future", "V1.0 — mature production integrations")):
        if name not in titles:
            gh("api", "--method", "POST", f"repos/{REPO}/milestones", "-f", f"title={name}", "-f", f"description={desc}")
            print(f"[repo] milestone {name}")


def issue_body(task: dict) -> str:
    acceptance = "\n".join(f"- [ ] {item}" for item in task["acceptance"])
    deps = ", ".join(task["depends"]) or "Nenhuma"
    return (f"**Fase:** {task['phase']} | **Prioridade:** {task['priority']} | **Marco:** {task['milestone']}\n\n"
            f"## Critérios de aceite\n{acceptance}\n\n"
            f"**Dependências:** {deps}\n\n"
            "**Done:** implementação, testes, evidências no PR e documentação necessária.")


def select_option(fields: dict, name: str, value: str) -> tuple[str, str] | None:
    field = fields.get(name)
    if not field:
        return None
    chosen = next((o for o in field.get("options", []) if o.get("name", "").lower() == value.lower()), None)
    return (field["id"], chosen["id"]) if chosen else None


def set_field(item_id: str, project_id: str, fields: dict, name: str, value: str) -> None:
    entry = select_option(fields, name, value)
    if entry is None:
        print(f"[warn] Campo/opção indisponível: {name}={value}")
        return
    field_id, option_id = entry
    gh("project", "item-edit", "--id", item_id, "--project-id", project_id,
       "--field-id", field_id, "--single-select-option-id", option_id)


def ensure_issues(number: int, project_id: str, fields: dict) -> None:
    seen = gh_json("issue", "list", "--repo", REPO, "--state", "all", "--limit", "200", "--json", "title,number,url")
    existing = {x["title"]: x["url"] for x in seen}
    counts = {"new": 0, "existing": 0}
    for task in BACKLOG:
        title = f"[{task['key']}] {task['title']}"
        url = existing.get(title)
        if not url:
            url = gh("issue", "create", "--repo", REPO, "--title", title,
                     "--body", issue_body(task), "--label", f"prio:{task['priority']}",
                     "--label", f"phase:{task['phase']}", "--label", "type:task",
                     "--milestone", task["milestone"])
            counts["new"] += 1
        else:
            counts["existing"] += 1
        item = gh_json("project", "item-add", str(number), "--owner", OWNER,
                       "--url", url, "--format", "json")
        item_id = item.get("id")
        if not item_id:
            print(f"[warn] Item sem ID: {task['key']} — {str(item)[:160]}")
            continue
        set_field(item_id, project_id, fields, "Priority", task["priority"])
        set_field(item_id, project_id, fields, "Phase", task["phase"])
        status = task["status"]
        if not select_option(fields, "Status", status):
            status = "Todo" if status in ("Backlog", "Ready") else status
        set_field(item_id, project_id, fields, "Status", status)
        print(f"[issue] {task['key']} ({task['priority']}, {task['status']}) {url}")
    print(f"[done] {counts['new']} novas issues, {counts['existing']} existentes")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap GitHub for Lab Control Panel")
    parser.add_argument("--dry-run", action="store_true", help="Preview backlog without network or writes")
    visibility = parser.add_mutually_exclusive_group()
    visibility.add_argument("--private", action="store_true", help="Create private repo (default: public)")
    args = parser.parse_args()

    if args.dry_run:
        print(f"Repository: {REPO} ({'private' if args.private else 'public'})")
        print(f"Project: {PROJECT_TITLE}; board: Backlog / Ready / In Progress / Review / Done")
        for item in BACKLOG:
            print(f"{item['key']} [{item['priority']}] ({item['phase']}, {item['status']}): {item['title']}")
        print(f"Total: {len(BACKLOG)} issues")
        return 0

    for executable in ("gh", "git"):
        if not shutil.which(executable):
            raise RuntimeError(f"Instale '{executable}' antes de executar o bootstrap.")
    if command("gh", "auth", "status", check=False).returncode:
        raise RuntimeError("Conecte a conta via 'gh auth login' antes de continuar.")
    login = gh("api", "user", "--jq", ".login")
    if login.lower() != OWNER.lower():
        raise RuntimeError(f"Conta autenticada: {login}. Esperado: {OWNER}. Nada foi alterado.")
    print(f"[auth] GitHub autenticado como {login}")
    if command("gh", "project", "list", "--owner", OWNER, "--format", "json", check=False).returncode:
        raise RuntimeError("Falta permissão de Projects: execute 'gh auth refresh -s project' e tente novamente. Nenhuma criação foi iniciada.")

    ensure_repo("private" if args.private else "public")
    ensure_labels()
    ensure_milestones()
    number, project_id, created = ensure_project("private" if args.private else "public")
    fields = ensure_fields(number, created)
    ensure_board_view(project_id, created)
    ensure_issues(number, project_id, fields)
    print(f"\nRepositório: https://github.com/{REPO}")
    print(f"Project: https://github.com/users/{OWNER}/projects/{number}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        sys.exit(1)
