
import argparse as ap
import logging

from .ui import HeadlessUI

parser = ap.ArgumentParser()
parser.add_argument('romfile', type=str, help='the ROM to load')
parser.add_argument('-v', '--verbose', action='store_true')
parser.add_argument('-d', '--debug', action='store_true')

args = parser.parse_args()

log_level = logging.WARNING
if args.verbose:
    log_level = logging.INFO
if args.debug:
    log_level = logging.DEBUG

ui = HeadlessUI(args.romfile, log_level=log_level)
ui.start()
