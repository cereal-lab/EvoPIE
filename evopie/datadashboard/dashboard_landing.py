# pylint: disable=no-member
# pylint: disable=E1101

from .. import models, APP # get also DB from there

import click

'''
This is a hypothetical landing page for the data dashboard.
The idea would be for all Winthrop/DataAnalysis pieces to go
in this datadashboard directory.
'''

@APP.route('/data-dashboard')
def dataDashboard():
    '''
    A test route to make sure we understand how to hook into the
    overall web server.  This simply displays a header message
    '''
    return '<html><body><h1>EvoPI Data Analysis Dashboard</h1></body></html>'
