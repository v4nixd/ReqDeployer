import sys

import api
import config

from console import console

DEBUG: bool = config.get("debug")

if __name__=="__main__":
    if sys.version_info < (3, 12):
        raise RuntimeError("Python 3.12 required!")
    
    if not DEBUG: console.clear()
    
    api.main()