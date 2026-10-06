import yfinance as yf


def baixar_dados(ticker, periodo="1y", auto_adjust=False):
    """Baixa dados diarios, com eventos corporativos e precos ajustados ou nominais."""
    dados = yf.download(
        ticker,
        period=periodo,
        auto_adjust=auto_adjust,
        actions=True,
        progress=False,
    )

    if dados.empty:
        raise RuntimeError(
            f"Nao foi possivel baixar dados para {ticker}. "
            "Verifique o ticker e a conexao com o Yahoo Finance."
        )

    # Algumas versoes do yfinance retornam MultiIndex mesmo para um ticker.
    if getattr(dados.columns, "nlevels", 1) > 1:
        dados = dados.droplevel("Ticker", axis=1)

    colunas_necessarias = {"Open", "Low", "Close", "Volume"}
    if not colunas_necessarias.issubset(dados.columns):
        raise ValueError(
            "Os dados baixados nao possuem as colunas necessarias: "
            f"{', '.join(sorted(colunas_necessarias))}."
        )

    # O yfinance pode omitir uma coluna de eventos quando ela nao existir no periodo.
    for coluna_evento in ("Dividends", "Stock Splits"):
        if coluna_evento not in dados.columns:
            dados[coluna_evento] = 0.0

    dados = dados.sort_index().dropna(subset=["Open", "Low", "Close", "Volume"])
    if len(dados) < 2:
        raise RuntimeError("Sao necessarios pelo menos dois pregoes para o backtest.")

    return dados


def executar_backtest(dados, queda_para_compra=0.01):
    """Compra em queda do fechamento anterior e vende no fechamento do dia."""
    if not 0 < queda_para_compra < 1:
        raise ValueError("queda_para_compra deve ser um valor entre 0 e 1.")

    trades_realizados = []

    for i in range(1, len(dados)):
        preco_fechamento_anterior = float(dados["Close"].iloc[i - 1])
        preco_abertura = float(dados["Open"].iloc[i])
        preco_minimo = float(dados["Low"].iloc[i])
        preco_venda = float(dados["Close"].iloc[i])
        preco_limite = preco_fechamento_anterior * (1 - queda_para_compra)

        if preco_abertura <= preco_limite:
            preco_compra = preco_abertura
            execucao = "abertura (gap)"
        elif preco_minimo <= preco_limite:
            preco_compra = preco_limite
            execucao = "limite intradiario"
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


def calcular_estatisticas(trades_realizados, dados):
    """Calcula metricas percentuais dos trades e volume financeiro medio."""
    total_trades = len(trades_realizados)
    volume_financeiro_medio = float((dados["Volume"] * dados["Close"]).mean())

    if total_trades == 0:
        return {
            "total_gain": 0,
            "percentual_gain": 0.0,
            "total_loss": 0,
            "percentual_loss": 0.0,
            "total_trades": 0,
            "resultado": 0.0,
            "maior_drawdown": 0.0,
            "max_drawdown": 0.0,
            "retorno_max_drawdown": 0.0,
            "data_max_drawdown": None,
            "ganho_maximo": 0.0,
            "ganho_medio": 0.0,
            "volume_financeiro_medio": volume_financeiro_medio,
            "trades_zero_a_zero": 0,
        }

    retornos = [trade["retorno"] for trade in trades_realizados]
    total_gain = sum(retorno > 0 for retorno in retornos)
    total_loss = sum(retorno < 0 for retorno in retornos)

    # Nesta implementacao alinhada a plataforma de referencia:
    # "max_drawdown" e "maior_drawdown" representam a MAIOR PERDA PERCENTUAL DE UMA UNICA OPERACAO
    # (menor retorno individual), e nao o drawdown classico de uma curva acumulada de pico a fundo.
    trade_pior = min(trades_realizados, key=lambda t: t["retorno"])
    menor_retorno = float(trade_pior["retorno"])
    max_drawdown = min(0.0, menor_retorno)
    data_max_drawdown = trade_pior["data"]
    retorno_max_drawdown = menor_retorno

    resultado = sum(retornos)
    return {
        "total_gain": total_gain,
        "percentual_gain": total_gain / total_trades * 100,
        "total_loss": total_loss,
        "percentual_loss": total_loss / total_trades * 100,
        "total_trades": total_trades,
        "resultado": resultado,
        "maior_drawdown": max_drawdown,
        "max_drawdown": max_drawdown,
        "retorno_max_drawdown": retorno_max_drawdown,
        "data_max_drawdown": data_max_drawdown,
        "ganho_maximo": max(retornos),
        "ganho_medio": resultado / total_trades,
        "volume_financeiro_medio": volume_financeiro_medio,
        "trades_zero_a_zero": total_trades - total_gain - total_loss,
    }


def obter_eventos_corporativos(dados, trades_realizados, queda_para_compra):
    """Relaciona eventos corporativos aos precos e ao eventual trade do dia."""
    trades_por_data = {trade["data"]: trade for trade in trades_realizados}
    eventos = []

    for i in range(1, len(dados)):
        dividendo = float(dados["Dividends"].iloc[i])
        split = float(dados["Stock Splits"].iloc[i])
        if dividendo == 0 and split == 0:
            continue

        data = dados.index[i]
        trade = trades_por_data.get(data)
        close_anterior = float(dados["Close"].iloc[i - 1])
        eventos.append(
            {
                "data": data,
                "close_anterior": close_anterior,
                "open": float(dados["Open"].iloc[i]),
                "low": float(dados["Low"].iloc[i]),
                "close": float(dados["Close"].iloc[i]),
                "preco_limite": close_anterior * (1 - queda_para_compra),
                "dividendo": dividendo,
                "split": split,
                "gerou_trade": trade is not None,
                "preco_compra": trade["preco_compra"] if trade else None,
                "retorno": trade["retorno"] if trade else None,
            }
        )

    return eventos


def relatorio(estatisticas, titulo="RELATORIO"):
    """Apresenta as estatisticas calculadas do backtest."""
    print(f"========== {titulo} ==========")
    print(f"Total Gain: {estatisticas['total_gain']}")
    print(f"% Gain: {estatisticas['percentual_gain']:.2f}%")
    print(f"Total Loss: {estatisticas['total_loss']}")
    print(f"% Loss: {estatisticas['percentual_loss']:.2f}%")
    print(f"Total Trades: {estatisticas['total_trades']}")
    print(f"Resultado: {estatisticas['resultado'] * 100:.2f}%")
    print(f"Max DrawDown: {estatisticas['max_drawdown'] * 100:.3f}%")

    print(f"Ganho Maximo: {estatisticas['ganho_maximo'] * 100:.2f}%")
    print(f"Ganho Medio: {estatisticas['ganho_medio'] * 100:.2f}%")
    print(
        "Volume Financeiro Medio: "
        f"{estatisticas['volume_financeiro_medio']:.2f}"
    )
    print(f"Trades no zero a zero: {estatisticas['trades_zero_a_zero']}")


def relatorio_eventos_corporativos(eventos):
    """Exibe o diagnostico dos dias com dividendo ou split."""
    print("========== EVENTOS CORPORATIVOS ==========")
    if not eventos:
        print("Nenhum dividendo ou split foi encontrado no periodo.")
        return

    for evento in eventos:
        preco_compra = (
            f"{evento['preco_compra']:.2f}"
            if evento["preco_compra"] is not None
            else "-"
        )
        retorno = (
            f"{evento['retorno'] * 100:.4f}%"
            if evento["retorno"] is not None
            else "-"
        )
        print(
            f"Data: {evento['data'].date()} | "
            f"Close anterior: {evento['close_anterior']:.2f} | "
            f"Open: {evento['open']:.2f} | Low: {evento['low']:.2f} | "
            f"Close: {evento['close']:.2f} | "
            f"Limite: {evento['preco_limite']:.2f} | "
            f"Dividendo: {evento['dividendo']:.4f} | "
            f"Split: {evento['split']:.4f} | "
            f"Trade: {'sim' if evento['gerou_trade'] else 'nao'} | "
            f"Compra: {preco_compra} | Retorno: {retorno}"
        )


def relatorio_comparativo(estatisticas_ajustadas, estatisticas_nominais):
    """Compara as metricas pedidas entre precos ajustados e nominais."""
    print("========== COMPARACAO DE PRECOS ==========")
    print(f"{'Metrica':<20} {'Ajustados':>15} {'Nominais':>15}")

    metricas = (
        ("Total Trades", "total_trades", "numero"),
        ("Total Gain", "total_gain", "numero"),
        ("Total Loss", "total_loss", "numero"),
        ("Resultado", "resultado", "percentual"),
        ("Max DrawDown", "max_drawdown", "percentual"),
        ("Ganho Maximo", "ganho_maximo", "percentual"),
        ("Ganho Medio", "ganho_medio", "percentual"),
    )
    for nome, chave, formato in metricas:
        valor_ajustado = estatisticas_ajustadas[chave]
        valor_nominal = estatisticas_nominais[chave]
        if formato == "percentual":
            texto_ajustado = f"{valor_ajustado * 100:.3f}%"
            texto_nominal = f"{valor_nominal * 100:.3f}%"
        else:
            texto_ajustado = str(valor_ajustado)
            texto_nominal = str(valor_nominal)
        print(f"{nome:<20} {texto_ajustado:>15} {texto_nominal:>15}")


def main():
    ticker = "VALE3.SA"
    periodo = "1y"
    queda_para_compra = 0.01

    # Configuracao principal: precos nominais, sem usar Adj Close na estrategia.
    dados_nominais = baixar_dados(ticker, periodo, auto_adjust=False)
    trades_nominais = executar_backtest(dados_nominais, queda_para_compra)
    estatisticas_nominais = calcular_estatisticas(trades_nominais, dados_nominais)

    # Comparacao diagnostica: os mesmos campos Open, Low e Close ajustados.
    dados_ajustados = baixar_dados(ticker, periodo, auto_adjust=True)
    trades_ajustados = executar_backtest(dados_ajustados, queda_para_compra)
    estatisticas_ajustadas = calcular_estatisticas(trades_ajustados, dados_ajustados)

    eventos = obter_eventos_corporativos(
        dados_nominais,
        trades_nominais,
        queda_para_compra,
    )

    relatorio(estatisticas_nominais, "RELATORIO - PRECOS NOMINAIS")
    relatorio_eventos_corporativos(eventos)
    relatorio_comparativo(estatisticas_ajustadas, estatisticas_nominais)


if __name__ == "__main__":
    main()
