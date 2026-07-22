import yfinance as yf

def main():

    dados = yf.download("PETR4.SA")
    
    dados = dados.droplevel("Ticker", axis=1)
    
    trades = 0
    lucro_total = 0

    for i in range(1, len(dados)):

        preco_hoje = dados["Close"].iloc[i]
        preco_ontem = dados["Close"].iloc[i - 1]
        variacao = (preco_hoje - preco_ontem) / preco_ontem
        
        
        if variacao <= -0.02:
            print("Compra!")
            print(f"Hoje: {preco_hoje}")
            print(f"Ontem: {preco_ontem}")
            print(f"Variacao: {variacao * 100}")
            print("-------")





if __name__ == "__main__":
    main()