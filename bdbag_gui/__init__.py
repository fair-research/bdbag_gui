import os
import sys

if getattr( sys, 'frozen', False ) :
        APP_DIR = sys._MEIPASS
else:
        APP_DIR = os.path.dirname(__file__)
