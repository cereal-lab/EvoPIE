from evopie import APP
from evopie.cli import DB_init, DB_populate

import debugpy
import os

# Winthrop testing page ...

if __name__ == '__main__':
    debug_mode = os.environ.get("DEBUG")
    if debug_mode == "True":
        # to enable remote debugging into the app: 
        print('DEBUGPY ACTIVELY LISTENING')
        debugpy.listen(("0.0.0.0", 5678))
        APP.run(debug=True)
    else:
        print('DEBUGPY NOT DOING ANYTHING')
        APP.run()
    APP.cli.add_command(DB_init)
    APP.cli.add_command(DB_populate)
