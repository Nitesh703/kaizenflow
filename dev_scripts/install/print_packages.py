#!/usr/bin/env python

import argparse
import logging
import os

import helpers.conda as hco
import helpers.dbg as dbg
import helpers.env as env
import helpers.io_ as io_
import helpers.printing as print_
import helpers.system_interaction as si

_LOG = logging.getLogger(__name__)


def _main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-v",
        dest="log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--conda_env_name", help="Environment name", default="develop", type=str
    )
    args = parser.parse_args()
    dbg.init_logger(verb=args.log_level, use_exec_path=True)
    msg = env.save_env_file(args.conda_env_name, dir_name=None)
    print(msg)


if __name__ == "__main__":
    _main()
