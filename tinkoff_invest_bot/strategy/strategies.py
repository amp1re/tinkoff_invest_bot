from math import floor
import time
import datetime

import pandas as pd

from tinkoff_invest_bot.api.client_service import ClientService
from tinkoff_invest_bot.data.fetchers import MMVBDataFetcher


class MMVBStrategy(MMVBDataFetcher, ClientService):
    """
    Initializes the MMVBStrategy class for managing and executing strategies on the MMVB index.

    Inherits from MMVBDataFetcher for fetching market data and ClientService for Tinkoff Invest API operations.

    Parameters
    ----------
    token : str
        The Tinkoff Invest API token.
    account_id : str
        The account ID for the Tinkoff Invest account.

    Attributes
    ----------
    url : str
        URL to fetch the MMVB index data.
    tickers_url : str
        URL to fetch share tickers information.
    money : Decimal or None
        The total money amount in the account's portfolio, fetched using ClientService's get_money method.

    Examples
    --------
    >>> strategy = MMVBStrategy(token='your_token', account_id='your_account_id')
    """

    def __init__(self, token, account_id):
        ClientService.__init__(self, token, account_id)
        MMVBDataFetcher.__init__(self)
        self.url = "https://smart-lab.ru/q/index_stocks/IMOEX/"
        self.tickers_url = "https://smart-lab.ru/q/shares/"
        self.money = self.get_money()

    def collect_mmvb_weights(self):
        """
        Collects and validates MMVB index data based on predefined URLs.

        Fetches MMVB index data from the URL specified in the `url` attribute,
        then validates this data against the tickers URL specified in the
        `tickers_url` attribute. The method leverages inherited capabilities
        from MMVBDataFetcher for fetching and validating the data.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the validated MMVB index data.

        Examples
        --------
        >>> strategy = MMVBStrategy(token='your_token', account_id='your_account_id')
        >>> mmvb_data = strategy.collect_mmvb_weights()
        >>> print(mmvb_data)
        """
        data_mmvb = self.fetch_index_data(self.url)
        data_mmvb = self.validate_data(data_mmvb, self.tickers_url)

        return data_mmvb

    def collect_portfolio_information(self):
        """
        Collects comprehensive portfolio information including positions, shares, and their last prices.

        Gathers data on the current positions using `get_positions_info`, retrieves information
        on shares from `get_shares_info`, and fetches the latest prices for these shares using
        `get_last_prices_info`. This method integrates functionalities from both inherited classes
        to compile a complete view of the portfolio.

        Returns
        -------
        tuple
            A tuple containing three pandas DataFrames: positions, shares, and prices information.

        Examples
        --------
        >>> strategy = MMVBStrategy(token='your_token', account_id='your_account_id')
        >>> positions, shares, prices = strategy.collect_portfolio_information()
        >>> print(positions, shares, prices)
        """
        self.postions = self.get_positions_info()
        self.shares = self.get_shares_info()
        self.prices = self.get_last_prices_info(self.shares["figi"].to_list())

        return self.postions, self.shares, self.prices

    def collect_information(self):
        """
        Aggregates comprehensive market and portfolio information into a single DataFrame.

        Sequentially calls `collect_mmvb_weights` to gather MMVB index data and
        `collect_portfolio_information` to fetch portfolio positions, shares, and their prices.
        Merges these datasets on common identifiers ('ticker' and 'figi') to create a unified view
        of the portfolio in relation to MMVB index constituents. Missing balance information
        is filled with zeros.

        Returns
        -------
        pd.DataFrame
            A unified DataFrame containing MMVB weights, share information, portfolio positions,
            and the latest share prices.

        Examples
        --------
        >>> strategy = MMVBStrategy(token='your_token', account_id='your_account_id')
        >>> combined_info = strategy.collect_information()
        >>> print(combined_info)
        """
        data = self.collect_mmvb_weights()
        positions, shares, prices = self.collect_portfolio_information()

        # Merge MMVB data with shares, positions, and prices for a comprehensive overview
        data = pd.merge(data, shares, how="left", on="ticker")
        data = pd.merge(data, positions, how="left", on="figi")
        data = pd.merge(data, prices, how="left", on="figi")

        # Fill missing balance data with zeros
        data["balance"] = data["balance"].fillna(0)
        return data

    def get_portfolio(self):
        """
        Computes and returns enhanced portfolio information, including calculated financial metrics.

        First, collects comprehensive market and portfolio information. Then, calculates additional
        financial metrics for each portfolio position, such as the price per lot, total value in rubles,
        portfolio weight by volume, and the ideal portfolio distribution based on MMVB index weights.
        It incorporates the total money in the account for weight calculations.

        Returns
        -------
        pd.DataFrame
            An enriched DataFrame containing original market and portfolio data along with
            calculated metrics: lot price, portfolio volume in rubles, portfolio weight by volume,
            and ideal portfolio values.

        Examples
        --------
        >>> strategy = MMVBStrategy(token='your_token', account_id='your_account_id')
        >>> portfolio_data = strategy.get_portfolio()
        >>> print(portfolio_data)
        """
        data = self.collect_information()

        # Calculate lot price and portfolio volume in rubles
        data["lot_price"] = data["price"] * data["lot"]
        data["portfolio_rubles_volume"] = data["price"] * data["balance"]

        # Calculate portfolio weight by volume and ideal portfolio distribution
        data["portfolio_weight_volume"] = (
            data["portfolio_rubles_volume"]
            / (data["portfolio_rubles_volume"].sum() + self.money)
        ) * 100
        data["ideal_portfolio"] = (
            data["weight"]
            / 100
            * (data["portfolio_rubles_volume"].sum() + self.money)
        )

        return data

    def search_shares_to_buy(self):
        """
        Identifies shares to buy based on the ideal portfolio distribution and current funds.

        Calculates the difference between the ideal portfolio and the current portfolio volume in rubles,
        determining which shares are candidates for purchase. Shares are considered for buying if the required
        investment is positive, does not exceed available funds, and can buy at least one lot. The method
        calculates the number of lots to buy for each share and returns this information.

        Returns
        -------
        dict
            A dictionary where keys are FIGIs and values are the number of lots to buy for each share.

        Examples
        --------
        >>> strategy = MMVBStrategy(token='your_token', account_id='your_account_id')
        >>> shares_to_buy = strategy.search_shares_to_buy()
        >>> print(shares_to_buy)
        """
        self.portfolio = self.get_portfolio()
        self.portfolio["to_buy_rubles"] = (
            self.portfolio["ideal_portfolio"]
            - self.portfolio["portfolio_rubles_volume"]
        ).apply(floor)
        self.portfolio["to_buy"] = (
            (self.portfolio["to_buy_rubles"] > 0)
            & (self.portfolio["lot_price"] <= self.money)
            & (self.portfolio["to_buy_rubles"] > self.portfolio["lot_price"])
        )

        self.adjusted_tickers = self.portfolio.loc[
            self.portfolio["to_buy"] == True
        ].copy()
        self.adjusted_tickers["lots_to_buy"] = (
            self.adjusted_tickers["to_buy_rubles"] // self.adjusted_tickers["lot_price"]
        ).astype("int")
        self.adjusted_tickers = (
            self.adjusted_tickers[["figi", "lots_to_buy"]]
            .set_index("figi")
            .to_dict()["lots_to_buy"]
        )

        return self.adjusted_tickers

    def run(self):
        """
        Execute the main trading loop.

        This method continuously checks whether the current day is a trading day and if the current
        time is within the trading hours as defined by the Moscow Exchange (MOEX). If it is a trading day
        and the current time is within trading hours, the method updates the available money, searches
        for shares to buy, and attempts to buy them. If no shares are identified for purchase or after
        attempting to buy shares, the method sleeps until the next day. The method handles exceptions
        gracefully by printing them and then continues by sleeping until the next day.

        Uses internal methods:
        - `moex_today_trading_schedule()` to get the trading day status and trading hours for the current day.
        - `get_money()` to update the available money.
        - `search_shares_to_buy()` to find shares to buy.
        - `buy_figi(figi, lot)` to buy a specific share identified by FIGI code and lot size.
        - `__sleep_to_next_day()` to sleep until 10:00 AM UTC of the next day.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        Exception
            Captures and prints any exceptions that occur during the execution of the trading loop.
        """
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        while True:
            try:
                is_trading_day, start_time, end_time = self.moex_today_trading_schedule()

                if is_trading_day and start_time < now < end_time:
                    print('Trading')
                    self.money = self.get_money()
                    self.share_to_buy = self.search_shares_to_buy()
                    print(self.share_to_buy)
                    if not self.share_to_buy:
                        print('No shares to buy')
                        self.__sleep_to_next_day()
                    else:
                        print('Start buy')
                        for figi, lot in self.share_to_buy.items():
                            self.buy_figi(figi, lot)
                            time.sleep(3)
            except Exception as e:
                print(e)
            print('Sleep for next day')
            self.__sleep_to_next_day()

    def __sleep_to(self, next_time: datetime.datetime):
        """
        Sleep until a specified future time.

        This method calculates the total number of seconds until a specified `next_time`
        and sleeps the current thread for that duration, if the `next_time` is in the future.

        Parameters
        ----------
        next_time : datetime.datetime
            The future time until which the current thread should sleep. It must be timezone-aware
            and is expected to be in UTC.

        Returns
        -------
        None
        """
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        total_seconds = (next_time - now).total_seconds()
        if total_seconds > 0:
            time.sleep(total_seconds)

    def __sleep_to_next_day(self):
        """
        Sleep until 10:00 AM UTC of the next day.

        This method calculates the time until 10:00 AM UTC of the next day from the current
        UTC time, and sleeps the current thread for that duration.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        future = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        next_time = datetime.datetime(
            year=future.year,
            month=future.month,
            day=future.day,
            hour=10,
            minute=0,
            tzinfo=datetime.timezone.utc,
        )

        self.__sleep_to(next_time)

