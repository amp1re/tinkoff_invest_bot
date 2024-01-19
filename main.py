from tinkoff_invest_bot.data.fetchers import MMVBDataFetcher

parser = MMVBDataFetcher()
url = "https://smart-lab.ru/q/index_stocks/IMOEX/"
tickers_url = "https://smart-lab.ru/q/shares/"


data = parser.fetch_index_data(url)
data = parser.validate_data(data, tickers_url)
print(data.head(3))
