from evopie import APP
from evopie.cli import DB_init, DB_populate

import debugpy
import os

# Winthrop testing page ...

if __name__ == '__main__':
    debug_mode = os.environ.get("EVOPIE_DEBUG")
    if debug_mode == "True":
        APP.run(debug=True)
    else:
        APP.run()
    APP.cli.add_command(DB_init)
    APP.cli.add_command(DB_populate)

