import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from suraj_dada.config.loader import get_config

if __name__ == "__main__":
    config = get_config()
    uvicorn.run(
        "suraj_dada.api.app:app",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.debug,
    )
