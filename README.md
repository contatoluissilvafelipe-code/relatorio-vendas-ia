# Relatório de vendas com IA

Transforma uma planilha de vendas (CSV) em um **relatório com resumo executivo**. As contas são feitas em código (confiável) e a IA só escreve o resumo em cima dos números calculados, o que evita números inventados.

## Como funciona
1. Lê `dados/vendas.csv` (data, produto, região, quantidade, valor unitário).
2. Calcula receita total, ticket médio, receita por mês, produto e região, e a variação do último mês.
3. Envia essas métricas (em JSON) ao LLM, pedindo 3 observações e 2 recomendações, sem inventar números. Sem chave de API, usa um modelo de texto.
4. Salva tudo em `relatorio.md`.

Os dados de exemplo são fictícios.

## Como rodar
Requer Python 3.9 ou superior.

```bash
python analisar.py --sem-llm    # sem API e sem custo
```

Com IA:

```bash
pip install -r requirements.txt
cp .env.example .env            # coloque sua ANTHROPIC_API_KEY dentro do .env
python analisar.py
```

Para usar seus dados: `python analisar.py meu_arquivo.csv` (mesmas colunas do exemplo).

## Testes
```bash
python -m unittest discover tests
```

## Próximos passos
- Gráficos no relatório e exportação em PDF.
- Envio automático do relatório por e-mail (por exemplo, com um fluxo no n8n).
