import os
import sys
from pkg_resources import get_distribution, DistributionNotFound

__version__ = "1.0.0b3"

try:
    VERSION = get_distribution("bdbag_gui").version
except DistributionNotFound:
    VERSION = __version__ + '-dev' if not getattr(sys, 'frozen', False) else __version__ + '-frozen'
