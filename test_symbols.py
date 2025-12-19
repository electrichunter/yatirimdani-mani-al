import yfinance as yf

symbols = ['XAUUSD=X', 'XAGUSD=X', 'XAU=X', 'XAG=X', 'GC=F', 'SI=F', 'PA=F', 'PL=F']

for s in symbols:
    try:
        data = yf.Ticker(s).history(period="1d")
        if not data.empty:
            print(f"{s}: ACTIVE - Current Price: {data['Close'].iloc[-1]}")
        else:
            print(f"{s}: NO DATA")
    except Exception as e:
        print(f"{s}: ERROR - {str(e)}")
