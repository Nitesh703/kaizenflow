import helpers.unit_test as hut
import vendors_amp.common.data.types as vcdtyp
import vendors_amp.ib.data.load.s3_data_loader as vidls3


class TestS3IbDataLoader1(hut.TestCase):
    """
    Test data loading correctness for Ib from S3.
    """

    def setUp(self) -> None:
        super().setUp()
        self._s3_data_loader = vidls3.S3IbDataLoader()

    def test_dtypes1(self) -> None:
        """
        Test column types of loaded dataframe.
        """
        # Load data.
        data = self._s3_data_loader.read_data(
            exchange="CME",
            symbol="ESZ21",
            asset_class=vcdtyp.AssetClass.Futures,
            frequency=vcdtyp.Frequency.Minutely,
            contract_type=vcdtyp.ContractType.Expiry,
            unadjusted=None,
            nrows=1,
        )
        # Get columns types.
        types = data.dtypes.to_string()
        # Compare with expected.
        self.check_string(types)

    def test_read_data1(self) -> None:
        """
        Test correctness of minute ESZ21 data loading.
        """
        # Load data.
        data = self._s3_data_loader.read_data(
            exchange="CME",
            symbol="ESZ21",
            asset_class=vcdtyp.AssetClass.Futures,
            frequency=vcdtyp.Frequency.Minutely,
            contract_type=vcdtyp.ContractType.Expiry,
            unadjusted=None,
            nrows=10,
        )
        # Transform dataframe to string.
        actual_string = hut.convert_df_to_string(data)
        # Compare with expected.
        self.check_string(actual_string)

    def test_read_data2(self) -> None:
        """
        Test correctness of minute TSLA data loading.
        """
        # Load data.
        data = self._s3_data_loader.read_data(
            exchange="NSDQ",
            symbol="TSLA",
            asset_class=vcdtyp.AssetClass.Stocks,
            frequency=vcdtyp.Frequency.Minutely,
            contract_type=vcdtyp.ContractType.Continuous,
            unadjusted=True,
            nrows=10,
        )
        # Transform dataframe to string.
        actual_string = hut.convert_df_to_string(data)
        # Compare with expected.
        self.check_string(actual_string)

    def test_read_data3(self) -> None:
        """
        Test correctness of daily CLH21 data loading.
        """
        # Load data.
        data = self._s3_data_loader.read_data(
            exchange="CME",
            symbol="CLH21",
            asset_class=vcdtyp.AssetClass.Futures,
            frequency=vcdtyp.Frequency.Daily,
            contract_type=vcdtyp.ContractType.Expiry,
            unadjusted=None,
            nrows=10,
        )
        # Transform dataframe to string.
        actual_string = hut.convert_df_to_string(data)
        # Compare with expected.
        self.check_string(actual_string)