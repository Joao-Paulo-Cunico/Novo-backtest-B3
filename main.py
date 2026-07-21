import yfinance as yf

def main():

    dados = yf.download("PETR4.SA")
    
    trades = 0
    lucro_total = 0
    print(dados)

    for i in range(1, len(dados)):

        preco_hoje = dados["Close"]["PETR4.SA"].iloc[i]
        preco_ontem = dados["Close"]["PETR4.SA"].iloc[i - 1]
        variacao = (preco_hoje - preco_ontem) / preco_ontem
        
        
        if variacao <= -0.02:
            print("Compra!")
            print(f"Hoje: {preco_hoje}")
            print(f"Ontem: {preco_ontem}")
            print(f"Variacao: {variacao * 100}")
            print("-------")





if __name__ == "__main__":
    main()