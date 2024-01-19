from abc import ABC, abstractmethod


class IndexDataFetcher(ABC):
    """
    Abstract base class for fetching index data.

    This class serves as a blueprint for classes that aim to fetch financial index data.
    Subclasses must implement the fetch_index_data method.

    Methods
    -------
    fetch_index_data()
        Abstract method for fetching index data. Must be implemented by subclasses.
    """

    @abstractmethod
    def fetch_index_data(self):
        """
        Fetch the data for a financial index.

        This is an abstract method that must be implemented by subclasses.
        The implementation should handle the process of retrieving index data
        from a specific source (e.g., an API, a database, etc.).

        Raises
        ------
        NotImplementedError
            If the subclass does not implement this method.
        """
        raise NotImplementedError(
            "The fetch_index_data method must be implemented by subclasses."
        )

    @abstractmethod
    def validate_data(self, data):
        """
        Validate the fetched financial index data.

        This abstract method should be implemented by subclasses to ensure that
        the data fetched by fetch_index_data is valid and conforms to expected formats
        and constraints.

        Parameters
        ----------
        data : pd.DataFrame
            The index data that needs to be validated.

        Raises
        ------
        NotImplementedError
            If the subclass does not implement this method.
        """
        raise NotImplementedError(
            "The validate_data method must be implemented by subclasses."
        )
