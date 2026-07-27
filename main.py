import yfinance as yf

def main():

    dados = yf.download("PETR4.SA")
    
    dados = dados.droplevel("Ticker", axis=1)
    
    trades = 0
    lucro_total = 0
    testevariacao = 0.01

    for i in range(1, len(dados)):

        preco_hoje = dados["Close"].iloc[i]
        preco_ontem = dados["Close"].iloc[i - 1]
        
        variacao = (preco_hoje - preco_ontem) / preco_ontem
        valor_compra = preco_ontem * (1 - testevariacao)
        lucro = preco_hoje - valor_compra
        
        
        if variacao <= testevariacao:
            trades += 1

            print("Compra!")
            
            print(f"Hoje: {preco_hoje:.2f}")
            print(f"Ontem: {preco_ontem:.2f}")
            print(f"Variacao: {variacao * 100:.2f}%\n" )

            print(f"Preco de compra: {valor_compra:.3f}")
            print(f"O lucro foi: {lucro:.2f}")

            print(f"{trades}")

            print("-------\n")




if __name__ == "__main__":
    main()