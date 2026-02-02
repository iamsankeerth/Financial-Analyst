import yfinance as yf
import matplotlib.pyplot as plt

# Define the stock symbol and timeframe
stock_symbol = 'AAPL'
timeframe = '1y'

# Download the stock data
stock_data = yf.download(stock_symbol, period=timeframe)

# Create the plot
plt.figure(figsize=(12, 6))
plt.plot(stock_data['Close'], label='AAPL Closing Price')
plt.title('AAPL Stock Performance for the Last Year')
plt.xlabel('Date')
plt.ylabel('Price (USD)')
plt.grid(True)
plt.legend()
plt.show()