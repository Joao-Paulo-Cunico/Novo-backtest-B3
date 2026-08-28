import yfinance as yf


def baixar_dados(ticker):
    dados = yf.download(ticker)
    dados = dados.droplevel("Ticker", axis=1)

    return dados


def executar_backtest(dados):
    trades_realizados = []

    print("Executando backtest...")
    lucro_total = 0
    trades_vencedores = 0
    # estatistica para operacao
    queda_para_compra = 0.01

    for i in range(1, len(dados)):
        preco_hoje = dados["Close"].iloc[i]
        preco_ontem = dados["Close"].iloc[i - 1]
        preco_minimo = dados["Low"].iloc[i]

        valor_compra = preco_ontem * (1 - queda_para_compra)
        lucro = preco_hoje - valor_compra

        if preco_minimo <= valor_compra:
            lucro_total += lucro

            if lucro > 0:
                trades_vencedores += 1

            trade = {
                "data": dados.index[i],
                "preco_compra": valor_compra,
                "preco_venda": preco_hoje,
                "lucro": lucro,
            }

            trades_realizados.append(trade)

    return trades_realizados, lucro_total


def calcular_estatisticas(trades_realizados):
    total_trades = len(trades_realizados)
    trades_vencedores = 0
    lucro_total = 0
    maior_lucro = None
    maior_prejuizo = None

    for trade in trades_realizados:
        lucro_total += trade["lucro"]
        lucro = trade["lucro"]

        if maior_lucro is None or lucro > maior_lucro:
            maior_lucro = lucro

        if maior_prejuizo is None or lucro < maior_prejuizo:
            maior_prejuizo = lucro

        if trade["lucro"] > 0:
            trades_vencedores += 1

    trades_perdedores = total_trades - trades_vencedores

    if total_trades > 0:
        taxa_acerto = (trades_vencedores / total_trades) * 100
        lucro_medio = lucro_total / total_trades
    else:
        taxa_acerto = 0
        lucro_medio = 0
        maior_lucro = 0
        maior_prejuizo = 0

    return (
        total_trades,
        trades_vencedores,
        trades_perdedores,
        lucro_total,
        lucro_medio,
        taxa_acerto,
        maior_lucro,
        maior_prejuizo,
    )


def relatorio(
    total_trades,
    trades_vencedores,
    trades_perdedores,
    lucro_total,
    lucro_medio,
    taxa_acerto,
    maior_lucro,
    maior_prejuizo
):
    print("========== RELATÓRIO ==========")
    print(f"Total de trades: {total_trades}")
    print(f"Trades vencedores: {trades_vencedores}")
    print(f"Trades perdedores: {trades_perdedores}")
    print(f"Lucro total: {lucro_total:.2f}")
    print(f"Lucro médio: {lucro_medio:.2f}")
    print(f"Taxa de acerto: {taxa_acerto:.2f}%")
    print(f"Maior lucro: {maior_lucro:.2f}")
    print(f"Maior prejuízo: {maior_prejuizo:.2f}")


def main():
    dados = baixar_dados("PETR4.SA")

    trades_realizados, lucro_total = executar_backtest(dados)

    (
        total_trades,
        trades_vencedores,
        trades_perdedores,
        lucro_total,
        lucro_medio,
        taxa_acerto,
        maior_lucro,
        maior_prejuizo
    ) = calcular_estatisticas(trades_realizados)

    relatorio(
        total_trades,
        trades_vencedores,
        trades_perdedores,
        lucro_total,
        lucro_medio,
        taxa_acerto,
        maior_lucro,
        maior_prejuizo
    )


if __name__ == "__main__":
    main()
