import sys

import api

if __name__=="__main__":
    if sys.version_info < (3, 12):
        raise RuntimeError("Python 3.12 required!")
    
    api.main()