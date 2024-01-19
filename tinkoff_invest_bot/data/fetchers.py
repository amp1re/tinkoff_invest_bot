from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup, element

from .base import IndexDataFetcher


class MMVBDataFetcher(IndexDataFetcher):
    """
    A class for fetching and parsing table data from a given URL.

    Attributes
    ----------
    url : str
        URL of the webpage to fetch data from.
    html : str, optional
        HTML content of the fetched webpage, initially None and cached after first fetch.

    Methods
    -------
    fetch_html():
        Fetches and returns the HTML content of the webpage.

    parse_table(table_index=0):
        Parses and returns the data of a specified table from the webpage as a pandas DataFrame.

    parse_table_data(table):
        Extracts and returns table data from a BeautifulSoup table object as a pandas DataFrame.

    validate_data(data, skip_rows=1, skip_start_columns=1, skip_end_columns=2):
        Validates and returns a modified pandas DataFrame based on specified trimming parameters.
    """

    def __init__(self):
        """
        Parameters
        ----------
        url : str
            The URL of the webpage from which to fetch data.
        """
        self.html: Optional[str] = None

    def fetch_html(self) -> Optional[str]:
        """
        Fetches and caches the HTML content of the webpage specified by the url attribute.

        Returns
        -------
        str or None
            HTML content of the webpage, or None if an error occurs during fetching.
        """
        if self.html is None:
            try:
                response = requests.get(self.url, timeout=10)  # Timeout added
                response.raise_for_status()
                self.html = response.text
            except requests.RequestException as e:
                print(f"Error fetching the webpage: {e}")
        return self.html

    def fetch_index_data(self, url, table_index: int = 0) -> Optional[pd.DataFrame]:
        """
        Parses a table from the fetched HTML content based on the specified index.

        Parameters
        ----------
        table_index : int, optional
            Index of the table to parse from the HTML (default is 0, which is the first table).

        Returns
        -------
        Optional[pd.DataFrame]
            DataFrame containing the parsed table data, or None if no table is found or an error occurs.
        """
        self.url = url
        html = self.fetch_html()
        if html:
            soup = BeautifulSoup(html, "html.parser")
            self.html = None
            tables = soup.find_all("table")
            if table_index < len(tables):
                return self.parse_table_data(tables[table_index])
            print(f"No table found at index {table_index}.")
            return None
        return None

    def parse_table_data(self, table: element.Tag) -> Optional[pd.DataFrame]:
        """
        Extracts data from a BeautifulSoup table object and converts it into a pandas DataFrame.

        Parameters
        ----------
        table : bs4.element.Tag
            BeautifulSoup object representing the HTML table to be parsed.

        Returns
        -------
        Optional[pd.DataFrame]
            DataFrame containing the parsed table data, or None if an error occurs during parsing.
        """
        try:
            headers = [th.text.strip() for th in table.find_all("th")]
            rows = [
                [td.text.strip() for td in tr.find_all("td")]
                for tr in table.find_all("tr")
            ]

            # Check if headers or rows are empty
            if not headers or not any(rows):
                print("Table headers or rows are empty.")
                return None

            return pd.DataFrame(columns=headers, data=rows)

        except AttributeError as e:
            print(f"Attribute error during parsing: {e}")
        except ValueError as e:
            print(f"Value error in DataFrame creation: {e}")
        except IndexError as e:
            print(f"Index error in parsing: {e}")
        return None

    def validate_data(
        self,
        data: pd.DataFrame,
        tickers_url: str,
        skip_rows: int = 1,
        skip_start_columns: int = 1,
        skip_end_columns: int = 2,
    ) -> Optional[pd.DataFrame]:
        """
        Validates and modifies the given DataFrame by trimming specified rows and columns.

        Parameters
        ----------
        data : pd.DataFrame
            DataFrame containing the data to be validated and modified.
        skip_rows : int, optional
            Number of initial rows to skip (default is 1).
        skip_start_columns : int, optional
            Number of initial columns to skip (default is 1).
        skip_end_columns : int, optional
            Number of final columns to skip (default is 2).

        Returns
        -------
        Optional[pd.DataFrame]
            Modified DataFrame after applying the trimming, or None if the input is not a DataFrame or is empty.
        """
        # Check if the data is a DataFrame
        if not isinstance(data, pd.DataFrame):
            print("Input is not a pandas DataFrame.")
            return None

        # Check if the DataFrame is empty
        if data.empty:
            print("DataFrame is empty.")
            return None
        validated_data = (
            data.iloc[skip_rows:, skip_start_columns:-skip_end_columns]
            if skip_end_columns > 0
            else data.iloc[skip_rows:, skip_start_columns:]
        )

        tickers_data = self.fetch_index_data(tickers_url)
        validated_data = pd.merge(
            validated_data,
            tickers_data[["Название", "Тикер"]],
            how="left",
            on="Название",
        )
        validated_data = validated_data[["Тикер", "Вес"]]
        validated_data = validated_data.rename(
            columns={"Тикер": "ticker", "Вес": "weight"}
        )
        validated_data["weight"] = (
            validated_data["weight"].apply(lambda x: x[:-1]).astype("float")
        )

        return validated_data
