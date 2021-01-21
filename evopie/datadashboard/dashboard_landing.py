# pylint: disable=no-member
# pylint: disable=E1101

from .. import models, APP # get also DB from there

import click
import os

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

    HTMLTextLines = []

    HTMLTextLines.append('<html>')
    HTMLTextLines.append('<head>')
    HTMLTextLines.append('  <title>EvoPIE Data Analysis Dashboard</title>')
    HTMLTextLines.append('</head>')
    HTMLTextLines.append('')
    HTMLTextLines.append('<body>')
    HTMLTextLines.append('  <h1>EvoPIE Data Analysis Dashboard</h1>')
    HTMLTextLines.append('  <p>Silly text</p>')

    # Here I'm just using the HTML page to see how to access the quizzes DB
    HTMLTextLines.append('  <samp>')
    myQuiz = models.Quiz()
    HTMLTextLines.append( str(myQuiz.dump_as_dict()) )
    HTMLTextLines.append('  </samp>')

    HTMLTextLines.append('</body>')
    HTMLTextLines.append('</html>')

    return os.linesep.join(HTMLTextLines)
