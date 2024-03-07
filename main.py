from bestconfig import Config

from tinkoff_invest_bot.strategy.strategies import MMVBStrategy

# data = parser.fetch_index_data(url)
# data = parser.validate_data(data, tickers_url)
# print(data.head(3))


config = Config()


token = config["INVEST_API"]["token"]  # pylint: disable=unsubscriptable-object
account_id = config["INVEST_API"][  # pylint: disable=unsubscriptable-object
    "account_id"
]

mmvb_strategy = MMVBStrategy(token=token, account_id=account_id)

# print(mmvb_strategy.search_shares_to_buy())

print(mmvb_strategy.moex_today_trading_schedule())

# client_service = ClientService(token, account_id)
# # print(client_service.get_positions_info())
# figi = client_service.get_positions_info()["figi"].to_list()
# #
# #
# #
# print(client_service.get_last_prices_info(figi))
