from evopie import APP
from evopie.utils import DB_init, DB_populate

if __name__ == '__main__':
    APP.run(debug=True)
    APP.cli.add_command(DB_init)
    APP.cli.add_command(DB_populate)