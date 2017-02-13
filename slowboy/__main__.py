
import argparse as ap

from .ui import HeadlessUI

parser = ap.ArgumentParser()
parser.add_argument('romfile', type=str, help='the ROM to load')
args = parser.parse_args()

ui = HeadlessUI(args.romfile)
ui.start()
