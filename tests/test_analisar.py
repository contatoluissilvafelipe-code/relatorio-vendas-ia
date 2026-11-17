import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import analisar  # noqa: E402

LINHAS = [
    {"mes": "2026-09", "produto": "A", "regiao": "Sul", "receita": 100.0, "quantidade": 1},
    {"mes": "2026-10", "produto": "A", "regiao": "Sul", "receita": 150.0, "quantidade": 1},
    {"mes": "2026-10", "produto": "B", "regiao": "Sudeste", "receita": 50.0, "quantidade": 1},
]


class TesteAnalise(unittest.TestCase):
    def test_metricas(self):
        m = analisar.calcular(LINHAS)
        self.assertEqual(m["receita_total"], 300.0)
        self.assertEqual(m["ticket_medio"], 100.0)
        self.assertEqual(next(iter(m["por_produto"])), "A")
        self.assertAlmostEqual(m["variacao_ultimo_mes_pct"], 100.0)

    def test_formato_moeda(self):
        self.assertEqual(analisar.brl(1234.5), "R$ 1.234,50")

    def test_carrega_csv_de_exemplo(self):
        linhas = analisar.carregar(RAIZ / "dados" / "vendas.csv")
        self.assertGreater(len(linhas), 0)
        self.assertEqual(len({l["mes"] for l in linhas}), 3)


if __name__ == "__main__":
    unittest.main()
