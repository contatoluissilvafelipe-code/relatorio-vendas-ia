"""Relatório de vendas com IA.

Calcula as métricas com código (confiável) e usa o LLM só para escrever o resumo executivo
em cima desses números. Sem chave de API, gera um resumo por modelo de texto.

Uso:
    python analisar.py                      # dados/vendas.csv
    python analisar.py outro_arquivo.csv
    python analisar.py --sem-llm
Saída: relatorio.md
"""
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

PASTA = Path(__file__).parent


def carregar_env() -> None:
    """Lê o arquivo .env (se existir) sem depender de bibliotecas externas."""
    arq = PASTA / ".env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                os.environ.setdefault(chave.strip(), valor.strip().strip("\"'"))


carregar_env()
MODELO = os.getenv("MODELO", "claude-sonnet-5-5")


def brl(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar(caminho: Path) -> list[dict]:
    with open(caminho, newline="", encoding="utf-8") as f:
        return [
            {
                "mes": l["data"][:7],
                "produto": l["produto"],
                "regiao": l["regiao"],
                "receita": int(l["quantidade"]) * float(l["valor_unitario"]),
                "quantidade": int(l["quantidade"]),
            }
            for l in csv.DictReader(f)
        ]


def somar(linhas: list[dict], chave: str) -> dict:
    total = defaultdict(float)
    for l in linhas:
        total[l[chave]] += l["receita"]
    return dict(total)


def calcular(linhas: list[dict]) -> dict:
    por_mes = dict(sorted(somar(linhas, "mes").items()))
    meses = list(por_mes)
    variacao = None
    if len(meses) >= 2 and por_mes[meses[-2]]:
        variacao = (por_mes[meses[-1]] / por_mes[meses[-2]] - 1) * 100
    receita = sum(l["receita"] for l in linhas)
    return {
        "receita_total": receita,
        "vendas": len(linhas),
        "ticket_medio": receita / len(linhas) if linhas else 0,
        "por_mes": por_mes,
        "por_produto": dict(sorted(somar(linhas, "produto").items(), key=lambda x: -x[1])),
        "por_regiao": dict(sorted(somar(linhas, "regiao").items(), key=lambda x: -x[1])),
        "variacao_ultimo_mes_pct": variacao,
    }


def resumo_modelo(m: dict) -> str:
    melhor = next(iter(m["por_produto"]))
    regiao = next(iter(m["por_regiao"]))
    txt = (
        f"No período, a receita foi de {brl(m['receita_total'])} em {m['vendas']} vendas "
        f"(ticket médio de {brl(m['ticket_medio'])}). O produto que mais vendeu foi {melhor} "
        f"e a região líder foi {regiao}."
    )
    if m["variacao_ultimo_mes_pct"] is not None:
        txt += f" A receita do último mês variou {m['variacao_ultimo_mes_pct']:+.1f}% em relação ao mês anterior."
    return txt


def resumo_llm(m: dict) -> str:
    import anthropic

    prompt = (
        "Você é analista de dados. Com base APENAS nas métricas em JSON abaixo, escreva em português "
        "um resumo executivo com 3 observações e 2 recomendações curtas. Não invente números.\n\n"
        + json.dumps(m, ensure_ascii=False, indent=2)
    )
    resp = anthropic.Anthropic().messages.create(
        model=MODELO, max_tokens=600, messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text.strip()


def montar_relatorio(m: dict, resumo: str, origem: str) -> str:
    def tabela(titulo, dados):
        linhas = "\n".join(f"| {k} | {brl(v)} |" for k, v in dados.items())
        return f"### {titulo}\n\n| Item | Receita |\n| --- | --- |\n{linhas}\n"

    return (
        f"# Relatório de vendas\n\n"
        f"- Receita total: **{brl(m['receita_total'])}**\n"
        f"- Vendas: **{m['vendas']}** | Ticket médio: **{brl(m['ticket_medio'])}**\n\n"
        f"## Resumo ({origem})\n\n{resumo}\n\n## Números\n\n"
        + tabela("Por mês", m["por_mes"])
        + "\n"
        + tabela("Por produto", m["por_produto"])
        + "\n"
        + tabela("Por região", m["por_regiao"])
    )


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    arquivo = Path(args[0]) if args else PASTA / "dados" / "vendas.csv"
    usar_llm = "--sem-llm" not in sys.argv and bool(os.getenv("ANTHROPIC_API_KEY"))
    metricas = calcular(carregar(arquivo))
    try:
        resumo, origem = (resumo_llm(metricas), "gerado por IA") if usar_llm else (resumo_modelo(metricas), "modelo de texto, sem IA")
    except Exception as erro:
        print(f"Falha na IA ({erro}); usando o modelo de texto")
        resumo, origem = resumo_modelo(metricas), "modelo de texto, sem IA"
    relatorio = montar_relatorio(metricas, resumo, origem)
    (PASTA / "relatorio.md").write_text(relatorio, encoding="utf-8")
    print(relatorio)
    print("Salvo em relatorio.md")


if __name__ == "__main__":
    main()
