import yfinance as yf


def baixar_dados(ticker, periodo="1y"):
    """Baixa OHLC diário sem ajustes para simular preços negociáveis."""
    dados = yf.download(ticker, period=periodo, auto_adjust=False, progress=False)

    if dados.empty:
        raise RuntimeError(
            f"Não foi possível baixar dados para {ticker}. "
            "Verifique o ticker e a conexão com o Yahoo Finance."
        )

    # yfinance devolve MultiIndex mesmo para um ticker em algumas versões.
    if getattr(dados.columns, "nlevels", 1) > 1:
        dados = dados.droplevel("Ticker", axis=1)

    colunas_necessarias = {"Open", "Low", "Close"}
    if not colunas_necessarias.issubset(dados.columns):
        raise ValueError(
            "Os dados baixados não possuem as colunas necessárias: "
            f"{', '.join(sorted(colunas_necessarias))}."
        )

    dados = dados.sort_index().dropna(subset=["Open", "Low", "Close"])
    if len(dados) < 2:
        raise RuntimeError("São necessários pelo menos dois pregões para o backtest.")

    return dados


def executar_backtest(dados, queda_para_compra=0.01):
    """Compra em -queda do fechamento anterior e vende no fechamento do dia."""
    if not 0 < queda_para_compra < 1:
        raise ValueError("queda_para_compra deve ser um valor entre 0 e 1.")

    trades_realizados = []

    for i in range(1, len(dados)):
        preco_ontem = float(dados["Close"].iloc[i - 1])
        preco_abertura = float(dados["Open"].iloc[i])
        preco_minimo = float(dados["Low"].iloc[i])
        preco_venda = float(dados["Close"].iloc[i])
        preco_limite = preco_ontem * (1 - queda_para_compra)

        # Uma ordem limite de compra é executada na abertura se houver gap para
        # baixo; caso contrário, é executada no preço limite ao ser tocado.
        if preco_abertura <= preco_limite:
            preco_compra = preco_abertura
            execucao = "abertura (gap)"
        elif preco_minimo <= preco_limite:
            preco_compra = preco_limite
            execucao = "limite intradiário"
        else:
            continue

        lucro = preco_venda - preco_compra
        retorno = lucro / preco_compra
        trades_realizados.append(
            {
                "data": dados.index[i],
                "preco_compra": preco_compra,
                "preco_venda": preco_venda,
                "lucro": lucro,
                "retorno": retorno,
                "execucao": execucao,
            }
        )

    return trades_realizados


def calcular_estatisticas(trades_realizados):
    """Calcula resultado e drawdown acumulados para uma ação por operação."""
    total_trades = len(trades_realizados)
    if total_trades == 0:
        return {
            "total_trades": 0, "trades_vencedores": 0, "trades_perdedores": 0,
            "trades_empate": 0, "lucro_total": 0.0, "lucro_medio": 0.0,
            "taxa_acerto": 0.0, "maior_lucro": 0.0, "maior_prejuizo": 0.0,
            "retorno_sobre_capital_movimentado": 0.0,
            "media_retorno_vencedores": 0.0, "media_retorno_perdedores": 0.0,
            "maior_drawdown": 0.0,
        }

    lucros = [trade["lucro"] for trade in trades_realizados]
    retornos = [trade["retorno"] for trade in trades_realizados]
    compras = [trade["preco_compra"] for trade in trades_realizados]
    vencedores = [retorno for retorno in retornos if retorno > 0]
    perdedores = [retorno for retorno in retornos if retorno < 0]

    # Cada trade representa uma ação. Não há simulação de capital ou reinvestimento.
    lucro_acumulado = 0.0
    pico_lucro = 0.0
    maior_drawdown = 0.0
    for lucro in lucros:
        lucro_acumulado += lucro
        pico_lucro = max(pico_lucro, lucro_acumulado)
        drawdown = lucro_acumulado - pico_lucro
        maior_drawdown = min(maior_drawdown, drawdown)

    lucro_total = sum(lucros)
    return {
        "total_trades": total_trades,
        "trades_vencedores": len(vencedores),
        "trades_perdedores": len(perdedores),
        "trades_empate": total_trades - len(vencedores) - len(perdedores),
        "lucro_total": lucro_total,
        "lucro_medio": lucro_total / total_trades,
        "taxa_acerto": len(vencedores) / total_trades * 100,
        "maior_lucro": max((lucro for lucro in lucros if lucro > 0), default=0.0),
        "maior_prejuizo": min((lucro for lucro in lucros if lucro < 0), default=0.0),
        "retorno_sobre_capital_movimentado": lucro_total / sum(compras),
        "media_retorno_vencedores": sum(vencedores) / len(vencedores) if vencedores else 0.0,
        "media_retorno_perdedores": sum(perdedores) / len(perdedores) if perdedores else 0.0,
        "maior_drawdown": maior_drawdown,
    }


def relatorio(estatisticas):
    print("========== RELATÓRIO ==========")
    print(f"Total de trades: {estatisticas['total_trades']}")
    print(f"Trades vencedores: {estatisticas['trades_vencedores']}")
    print(f"Trades perdedores: {estatisticas['trades_perdedores']}")
    print(f"Trades no zero a zero: {estatisticas['trades_empate']}")
    print(f"Lucro total por ação: {estatisticas['lucro_total']:.2f}")
    print(f"Lucro médio por ação: {estatisticas['lucro_medio']:.2f}")
    print(f"Taxa de acerto: {estatisticas['taxa_acerto']:.2f}%")
    print(f"Maior lucro por ação: {estatisticas['maior_lucro']:.2f}")
    print(f"Maior prejuízo por ação: {estatisticas['maior_prejuizo']:.2f}")
    print("Retorno sobre capital movimentado: " f"{estatisticas['retorno_sobre_capital_movimentado'] * 100:.2f}%")
    print("Média dos vencedores: " f"{estatisticas['media_retorno_vencedores'] * 100:.2f}%")
    print("Média dos perdedores: " f"{estatisticas['media_retorno_perdedores'] * 100:.2f}%")
    print(f"Maior drawdown acumulado por ação: {estatisticas['maior_drawdown']:.2f}")


def main():
    dados = baixar_dados("VALE3.SA", periodo="1y")
    trades_realizados = executar_backtest(dados, queda_para_compra=0.01)
    relatorio(calcular_estatisticas(trades_realizados))


if __name__ == "__main__":
    main()
