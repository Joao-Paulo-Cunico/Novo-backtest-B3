import yfinance as yf


def baixar_dados(ticker):
    dados = yf.download(ticker)
    dados = dados.droplevel("Ticker", axis=1)

    return dados


def executar_backtest(dados):
    trades_realizados = []
    
    print("Executando backtest...")
    trades = 0
    lucro_total = 0
    trades_vencedores = 0
    queda_para_compra = 0.02

    for i in range(1, len(dados)):
        preco_hoje = dados["Close"].iloc[i]
        preco_ontem = dados["Close"].iloc[i - 1]

        variacao = (preco_hoje - preco_ontem) / preco_ontem
        valor_compra = preco_ontem * (1 - queda_para_compra)
        lucro = preco_hoje - valor_compra

        if variacao <= -queda_para_compra:
            lucro_total += lucro
            trades += 1

            if lucro > 0:
                trades_vencedores += 1
                
            trade = {
                "data": dados.index[i],
                "preco_compra": valor_compra,
                "preco_venda": preco_hoje,
                "lucro": lucro
            }

            trades_realizados.append(trade)

    if trades > 0:
        taxa_acerto = (trades_vencedores / trades) * 100
    else:
        taxa_acerto = 0


    return trades_realizados, trades, lucro_total, taxa_acerto


def relatorio(trades, lucro_total, taxa_acerto):
    print("========== RELATÓRIO ==========")
    print(f"Total de trades: {trades}")
    print(f"Lucro total: {lucro_total:.2f}")
    print(f"Taxa de acerto: {taxa_acerto:.2f}%")


def main():
    dados = baixar_dados("VALE3.SA")

    print(dados.columns)
    print(type(dados["Close"]))
    print(dados["Close"].head())
    

    trades_realizados, trades, lucro_total, taxa_acerto = executar_backtest(dados)
    relatorio(trades, lucro_total, taxa_acerto)
    
    print(trades_realizados[0]["lucro"])


if __name__ == "__main__":
    main()
