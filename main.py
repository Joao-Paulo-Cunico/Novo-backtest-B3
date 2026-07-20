import yfinance as yf

def main():

    dados = yf.download("PETR4.SA")

    for i in range(1, len(dados)):

        preco_hoje = dados["Close"].iloc[i]
        preco_ontem = dados["Close"].iloc[i - 1]

        print(preco_hoje)
        print(preco_ontem)
        print()




if __name__ == "__main__":
    main()