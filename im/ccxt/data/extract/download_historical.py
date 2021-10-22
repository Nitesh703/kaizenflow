#!/usr/bin/env python
"""
Script to download historical data from CCXT.

Use as:

# Download Binance BTC/USDT data from 2019-01-01 to 2019-01-02:
> download_historical.py \
     --dst_dir test \
     --exchange_ids "binance" \
     --currency_pairs "BTC/USDT" \
     --start_datetime "2019-01-01" \
     --end_datetime "2019-01-02"

# Download Binance data from 2019-01-01 to now,
  for all currency pairs:
> download_historical.py \
     --dst_dir test \
     --exchange_ids "binance" \
     --currency_pairs "all" \
     --start_datetime "2019-01-01" \

# Download data for all exchanges, BTC/USDT and ETH/USDT currency pairs,
  from 2019-01-01 to now:
> download_historical.py \
     --dst_dir test \
     --exchange_ids "all" \
     --currency_pairs "BTC/USDT ETH/USDT" \
     --start_datetime "2019-01-01" \

# Download data for all exchanges and all pairs, from 2019-01-01 to 2019-01-02:
> download_historical.py \
     --dst_dir test \
     --exchange_ids "all" \
     --currency_pairs "all" \
     --start_datetime "2019-01-01" \
     --start_endtime "2019-01-02"

Import as:

import im.ccxt.data.extract.download_historical as imcdaexdowhis
"""

import argparse
import logging
import os
import time

import pandas as pd

import helpers.dbg as hdbg
import helpers.io_ as hio
import helpers.parser as hparser
import im.ccxt.data.extract.exchange_class as imcdaexexccla

_LOG = logging.getLogger(__name__)

_ALL_EXCHANGE_IDS = ["binance", "kucoin"]


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--dst_dir",
        action="store",
        required=True,
        type=str,
        help="Folder to download files to",
    )
    parser.add_argument(
        "--api_keys",
        action="store",
        type=str,
        default=imcdaexexccla.API_KEYS_PATH,
        help="Path to JSON file that contains API keys for exchange access",
    )
    parser.add_argument(
        "--exchange_ids",
        action="store",
        required=True,
        type=str,
        help="CCXT exchange ids to download data for separated by spaces, e.g. 'binance gemini',"
        "'all' for all supported exchanges",
    )
    parser.add_argument(
        "--currency_pairs",
        action="store",
        required=True,
        type=str,
        help="Name of the currency pair to download data for, separated by spaces,"
        " e.g. 'BTC/USD ETH/USD','all' for all the currency pairs in exchange",
    )
    parser.add_argument(
        "--start_datetime",
        action="store",
        required=True,
        type=str,
        help="Start date of download in iso8601 format, e.g. '2021-09-08T00:00:00.000Z'",
    )
    parser.add_argument(
        "--end_datetime",
        action="store",
        type=str,
        default=None,
        help="End date of download in iso8601 format, e.g. '2021-10-08T00:00:00.000Z'."
        "None means datetime.now())",
    )
    parser.add_argument(
        "--step",
        action="store",
        type=int,
        default=None,
        help="Size of each API request per iteration",
    )
    parser.add_argument(
        "--sleep_time",
        action="store",
        type=int,
        default=60,
        help="Sleep time between currency pair downloads (in seconds).",
    )
    parser.add_argument("--incremental", action="store_true")
    parser = hparser.add_verbosity_arg(parser)
    return parser  # type: ignore[no-any-return]


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Create the directory.
    hio.create_dir(args.dst_dir, incremental=args.incremental)
    # Pick start and end datetime.
    start_datetime = pd.Timestamp(args.start_datetime)
    if not args.end_datetime:
        # If end datetime is not provided, get current time.
        end_datetime = pd.Timestamp.now()
    else:
        end_datetime = pd.Timestamp(args.end_datetime)
    # Pick the exchanges.
    if args.exchange_ids == "all":
        # Iterate over all the available exchanges.
        exchange_ids = _ALL_EXCHANGE_IDS
    else:
        # Get a single exchange.
        exchange_ids = args.exchange_ids.split()
    _LOG.info("Getting data for exchanges %s", ", ".join(exchange_ids))
    for exchange_id in exchange_ids:
        # Initialize the exchange class.
        exchange = imcdaexexccla.CcxtExchange(exchange_id, api_keys_path=args.api_keys)
        if args.currency_pairs == "all":
            # Iterate over all currencies available for exchange.
            present_pairs = exchange.currency_pairs
        else:
            # Iterate over provided currency.
            currency_pairs = args.currency_pairs.split()
            # Leave only currencies present in exchange.
            present_pairs = [
                curr for curr in currency_pairs if curr in exchange.currency_pairs
            ]
            # Warn if not all passed currencies are present.
            if len(present_pairs) != len(currency_pairs):
                _LOG.warning(
                    "Currencies %s not present in exchange %s!",
                    list(set.difference(set(currency_pairs), set(present_pairs))),
                    exchange_id,
                )
        _LOG.debug("Getting data for currencies %s", ", ".join(present_pairs))
        for pair in present_pairs:
            # Download OHLCV data.
            pair_data = exchange.download_ohlcv_data(
                curr_symbol=pair,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                step=args.step,
            )
            # Sleep between iterations.
            time.sleep(args.sleep_time)
            # Create file name based on exchange and pair.
            # E.g. 'binance_BTC_USDT.csv.gz'
            file_name = f"{exchange_id}_{pair.replace('/', '_')}.csv.gz"
            full_path = os.path.join(args.dst_dir, file_name)
            # Save file.
            pair_data.to_csv(
                full_path,
                index=False,
                compression="gzip",
            )
            _LOG.debug("Saved data to %s", file_name)


if __name__ == "__main__":
    _main(_parse())