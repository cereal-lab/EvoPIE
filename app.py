from evopie import APP
from evopie.cli import DB_init, DB_populate
from datetime import datetime

# Winthrop testing page ...
import evopie.datadashboard.dashboard_landing

def date(d):
    return d.strftime("%B %d, %Y by %I:%M %p")

APP.add_template_filter(date)



if __name__ == '__main__':
    APP.run(debug=True)
    APP.cli.add_command(DB_init)
    APP.cli.add_command(DB_populate)
