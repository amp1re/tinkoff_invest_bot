from bestconfig import Config

from tinkoff_invest_bot.api.client_service import ClientService
from tinkoff_invest_bot.data.fetchers import MMVBDataFetcher

parser = MMVBDataFetcher()
url = "https://smart-lab.ru/q/index_stocks/IMOEX/"
tickers_url = "https://smart-lab.ru/q/shares/"


# data = parser.fetch_index_data(url)
# data = parser.validate_data(data, tickers_url)
# print(data.head(3))


config = Config()


token = config["INVEST_API"]["token"]  # pylint: disable=unsubscriptable-object
account_id = config["INVEST_API"]["account_id"]  # pylint: disable=unsubscriptable-object

client_service = ClientService(token, account_id)
# print(client_service.get_positions_info())
figi = client_service.get_positions_info()["figi"].to_list()
#
#
#
print(client_service.get_last_prices_info(figi))
