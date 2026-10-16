"""Avisa por uma issue do GitHub quando a coleta diária quebra, e fecha o aviso quando ela volta.

Uso (no GitHub Actions):
    python -m scraper.alertas falhou --log coleta.log
    python -m scraper.alertas resolvida

Só usa a biblioteca padrão do Python: precisa funcionar justamente quando a instalação das
dependências (pip) é o que falhou.

Variáveis de ambiente (o Actions preenche quase todas sozinho):
- GITHUB_TOKEN: token com permissão `issues: write` (o workflow passa o dele)
- GITHUB_REPOSITORY, GITHUB_SERVER_URL, GITHUB_API_URL, GITHUB_RUN_ID: de onde e qual execução
- PASSOS: o `toJSON(steps)` do workflow, para dizer qual etapa falhou
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROTULO = "coleta-quebrada"
TITULO = "A coleta diária de imóveis falhou"
LINHAS_DO_LOG = 60
FUSO_BRASILIA = timezone(timedelta(hours=-3))
# Nome de cada etapa do workflow, pelo `id` dela em .github/workflows/main.yml
ETAPAS = {
    "dependencias": "Instalar dependências do scraper",
    "scraper": "Rodar o scraper",
    "csv": "Commit e push do CSV atualizado",
    "snapshot": "Guardar snapshot do dia no histórico",
}


class GitHub:
    """O pouco da API de issues do GitHub que o alerta usa."""

    def __init__(self, repositorio: str, token: str, api: str = "https://api.github.com"):
        self.base = f"{api.rstrip('/')}/repos/{repositorio}"
        self.token = token

    def _pedir(self, metodo: str, caminho: str, dados: dict | None = None):
        corpo = json.dumps(dados).encode() if dados is not None else None
        pedido = Request(f"{self.base}{caminho}", data=corpo, method=metodo, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "imobiliario-universitario-alertas",
        })
        with urlopen(pedido, timeout=30) as resposta:
            return json.load(resposta)

    def issues_abertas(self) -> list[dict]:
        issues = self._pedir("GET", f"/issues?labels={ROTULO}&state=open&per_page=100")
        return [issue for issue in issues if "pull_request" not in issue]  # a API mistura PRs nas issues

    def abrir(self, titulo: str, texto: str) -> dict:
        # Se o rótulo ainda não existir no repositório, o GitHub cria na hora
        return self._pedir("POST", "/issues", {"title": titulo, "body": texto, "labels": [ROTULO]})

    def comentar(self, numero: int, texto: str) -> dict:
        return self._pedir("POST", f"/issues/{numero}/comments", {"body": texto})

    def fechar(self, numero: int) -> dict:
        return self._pedir("PATCH", f"/issues/{numero}", {"state": "closed", "state_reason": "completed"})


def link_da_execucao(ambiente) -> str:
    servidor = ambiente.get("GITHUB_SERVER_URL", "https://github.com")
    return f"{servidor}/{ambiente.get('GITHUB_REPOSITORY', '')}/actions/runs/{ambiente.get('GITHUB_RUN_ID', '')}"


def etapas_que_falharam(passos_json: str | None) -> list[str]:
    """Nomes das etapas com resultado "failure", a partir do toJSON(steps) do workflow."""
    try:
        passos = json.loads(passos_json or "{}")
    except json.JSONDecodeError:
        return []
    return [ETAPAS.get(passo, passo) for passo, estado in passos.items() if estado.get("outcome") == "failure"]


def fim_do_log(caminho: Path | None, linhas: int = LINHAS_DO_LOG) -> str | None:
    if not caminho or not caminho.exists():
        return None
    texto = caminho.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(texto[-linhas:])


def texto_da_falha(link: str, etapas: list[str], log: str | None, agora: datetime) -> str:
    etapa = ", ".join(f"**{nome}**" for nome in etapas) or "uma etapa de preparação (checkout ou Python)"
    partes = [
        f"**{agora:%d/%m/%Y %H:%M}** (horário de Brasília): a coleta falhou.",
        "",
        f"- Execução: {link}",
        f"- Etapa que falhou: {etapa}",
        "- O HTML das páginas que não puderam ser lidas, se houver, está no artefato `paginas-com-falha` "
        "da execução.",
        "",
        "Enquanto isso, o dashboard continua mostrando a última coleta que deu certo.",
    ]
    if log:
        partes += ["", f"<details><summary>Fim do log da coleta</summary>\n\n```\n{log}\n```\n</details>"]
    return "\n".join(partes)


def avisar_falha(github: GitHub, texto: str) -> str:
    """Comenta na issue que já está aberta ou abre uma nova. Devolve o que foi feito."""
    abertas = github.issues_abertas()
    if abertas:
        numero = abertas[0]["number"]
        github.comentar(numero, texto)
        return f"comentado na issue #{numero}"
    issue = github.abrir(TITULO, texto)
    return f"aberta a issue #{issue['number']}"


def fechar_avisos(github: GitHub, link: str, agora: datetime) -> list[int]:
    """Fecha as issues de coleta quebrada, se houver, e devolve os números delas."""
    fechadas = []
    for issue in github.issues_abertas():
        github.comentar(issue["number"], f"**{agora:%d/%m/%Y %H:%M}**: a coleta voltou a funcionar ({link}).")
        github.fechar(issue["number"])
        fechadas.append(issue["number"])
    return fechadas


def main(argv: list[str] | None = None, ambiente=None) -> int:
    ambiente = os.environ if ambiente is None else ambiente
    parser = argparse.ArgumentParser(description="Avisa (ou fecha o aviso) de coleta quebrada por issue.")
    parser.add_argument("situacao", choices=["falhou", "resolvida"])
    parser.add_argument("--log", type=Path, help="log da coleta, para mostrar o final dele na issue")
    args = parser.parse_args(argv)

    if not ambiente.get("GITHUB_TOKEN") or not ambiente.get("GITHUB_REPOSITORY"):
        print("GITHUB_TOKEN e GITHUB_REPOSITORY são necessários (rode no GitHub Actions)", file=sys.stderr)
        return 2
    github = GitHub(ambiente["GITHUB_REPOSITORY"], ambiente["GITHUB_TOKEN"],
                    ambiente.get("GITHUB_API_URL", "https://api.github.com"))
    agora = datetime.now(FUSO_BRASILIA)
    if args.situacao == "falhou":
        texto = texto_da_falha(link_da_execucao(ambiente), etapas_que_falharam(ambiente.get("PASSOS")),
                               fim_do_log(args.log), agora)
        print(avisar_falha(github, texto))
    else:
        fechadas = fechar_avisos(github, link_da_execucao(ambiente), agora)
        print("fechadas: " + ", ".join(f"#{numero}" for numero in fechadas) if fechadas else "nenhum aviso aberto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
