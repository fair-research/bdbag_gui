import os
import sys
from pkg_resources import get_distribution, DistributionNotFound

try:
    VERSION = get_distribution("bdbag_gui").version
except DistributionNotFound:
    VERSION = '0.0.dev0'

if getattr(sys, 'frozen', False):
        APP_DIR = getattr(sys, '_MEIPASS')
else:
        APP_DIR = os.path.dirname(__file__)
