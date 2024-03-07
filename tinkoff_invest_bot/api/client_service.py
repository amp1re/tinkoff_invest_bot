import datetime
from typing import List

import pandas as pd
from tinkoff.invest import Client, OrderDirection, OrderType, RequestError

from tinkoff_invest_bot.utils import cast_money


class ClientService:
    """
    A service class for interacting with the Tinkoff Invest API.

    Provides simplified access to trading operations, account management,
    and market data retrieval through the Tinkoff Invest API.

    Attributes
    ----------
    __token : str
        The API token for authentication.
    __account_id : str
        The account ID for operations.
    """

    def __init__(self, token: str, account_id: str) -> None:
        """
        Initializes the ClientService with a given token and account ID.

        Parameters
        ----------
        token : str
            The API token for Tinkoff Invest authentication.
        account_id : str
            The account ID for performing operations.
        """
        self.__token = token
        self.__account_id = account_id

    def get_shares_info(self) -> pd.DataFrame:
        """
        Retrieves information about available shares from the Tinkoff Invest API.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the ticker, FIGI, and lot size of each share.
        """
        with Client(self.__token) as client:
            try:
                shares = client.instruments.shares().instruments
                shares_info = [
                    {"ticker": item.ticker, "figi": item.figi, "lot": item.lot}
                    for item in shares
                ]
                return pd.DataFrame(shares_info)
            except Exception as e:
                print(f"Failed to retrieve shares information: {e}")
                return pd.DataFrame()  # Return an empty DataFrame in case of failure

    def get_positions_info(self) -> pd.DataFrame:
        """
        Retrieves information about the current positions (securities) for the specified account.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the FIGI and balance of each security position.
        """
        with Client(self.__token) as client:
            try:
                positions = client.operations.get_positions(
                    account_id=self.__account_id
                ).securities
                positions_info = [
                    {
                        "figi": pos.figi,
                        "balance": pos.balance if pos.balance is not None else 0,
                    }
                    for pos in positions
                ]
                return pd.DataFrame(positions_info)
            except Exception as e:
                print(f"Failed to retrieve positions information: {e}")
                return pd.DataFrame()  # Return an empty DataFrame in case of failure

    def get_last_prices_info(self, figi: List[str]) -> pd.DataFrame:
        """
        Retrieves the last known prices for a list of financial instruments identified by their FIGI.

        Parameters
        ----------
        figi : List[str]
            A list of FIGI (Financial Instrument Global Identifier) codes for which to retrieve the last prices.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the FIGI and last price for each requested financial instrument.

        Raises
        ------
        ValueError
            If the input is not a list or is an empty list.
        """
        if not figi or not isinstance(figi, list):
            raise ValueError("Input must be a non-empty list of FIGI codes.")

        with Client(self.__token) as client:
            try:
                prices = client.market_data.get_last_prices(
                    instrument_id=figi
                ).last_prices
                prices_info = [
                    {"figi": price.figi, "price": cast_money(price.price)}
                    for price in prices
                ]
                return pd.DataFrame(prices_info)
            except Exception as e:
                print(f"Failed to retrieve last prices information: {e}")
                return pd.DataFrame()  # Return an empty DataFrame in case of failure

    def get_money(self):
        """
        Retrieves the total amount of money in the specified account's portfolio.

        This method connects to the Tinkoff Invest API using the provided token and account ID,
        and fetches the total amount of all currencies in the portfolio, converting the value
        to a decimal representation for precision.

        Returns
        -------
        Decimal or None
            The total money amount in the account's portfolio as a Decimal, or None if the
            retrieval fails.

        Examples
        --------
        >>> client_service = ClientService(token='your_token', account_id='your_account_id')
        >>> total_money = client_service.get_money()
        >>> print(total_money)

        Notes
        -----
        The method catches and prints any exceptions that occur during the API call, returning
        None in case of failure to allow for graceful error handling by the caller.
        """
        with Client(self.__token) as client:
            try:
                money = client.operations.get_portfolio(account_id=self.__account_id)
                money = cast_money(money.total_amount_currencies)
                return money
            except Exception as e:
                print(f"Failed to retrieve money information: {e}")
                return None

    def byu_figi(self, figi, lot):
        """
        Executes a market buy order for a financial instrument identified by its FIGI.

        Parameters
        ----------
        figi : str
            The FIGI (Financial Instrument Global Identifier) code of the financial instrument to buy.
        lot : int
            The number of lots to buy.

        Raises
        ------
        RequestError
            If there is an error in executing the buy order.

        """
        try:
            with Client(self.__token) as client:
                client.orders.post_order(
                    order_id=str(datetime.datetime.utcnow().timestamp()),
                    figi=figi,
                    quantity=lot,
                    account_id=self.__account_id,
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                )

        except RequestError as e:
            print(str(e))

    def __trading_schedules(
        self, exchange: str, _from: datetime.datetime, _to: datetime.datetime
    ):
        """
        Retrieve trading schedules for a specific exchange within a given time range.

        Parameters
        ----------
        exchange : str
            The name of the exchange.
        _from : datetime
            The start date/time for retrieving trading schedules.
        _to : datetime
            The end date/time for retrieving trading schedules.

        Returns
        -------
        list
            A list of trading schedules for the specified exchange within the given time range.
        """
        result = []
        with Client(self.__token) as client:
            try:
                for schedule in client.instruments.trading_schedules(
                    exchange=exchange, from_=_from, to=_to
                ).exchanges:
                    result.append(schedule)
            except Exception as e:
                print(f"Failed to retrieve trading schedules: {e}")
        return result

    def moex_today_trading_schedule(self):
        """
        Retrieves the trading schedule for MOEX for the current day.

        Returns
        -------
        tuple
            A tuple containing the following information:
            - is_trading_day: bool, indicating if it is a trading day
            - start_time: datetime, the start time of trading
            - end_time: datetime, the end time of trading

        """
        for schedule in self.__trading_schedules(
            exchange="MOEX",
            _from=datetime.datetime.utcnow(),
            _to=datetime.datetime.utcnow() + datetime.timedelta(days=1),
        ):
            for day in schedule.days:
                if day.date.date() == datetime.date.today():
                    return day.is_trading_day, day.start_time, day.end_time

        return False, datetime.datetime.utcnow(), datetime.datetime.utcnow()
