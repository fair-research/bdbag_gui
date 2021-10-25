import os
import sys
from pkg_resources import get_distribution, DistributionNotFound

__version__ = "1.2.0"

try:
    version = get_distribution("bdbag_gui").version
    VERSION = version + '' if not getattr(sys, 'frozen', False) else version + '-frozen'
except DistributionNotFound:
    VERSION = __version__ + '-dev' if not getattr(sys, 'frozen', False) else __version__ + '-frozen'
