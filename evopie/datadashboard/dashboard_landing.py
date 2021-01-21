# pylint: disable=no-member
# pylint: disable=E1101

from .. import models, APP # get also DB from there

import click
import os

# For My plotly testing:
try:
  import plotly.express as px
  import plotly.io as pio
except:
  pass

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
    # Render out an HTML file with the a test interactive boxplot
    boxplotHTML = ""
    try:
      df = px.data.tips()  # Pre-loaded data that comes in plotly.express
      fig = px.box(df, x="time", y="total_bill", points="all")
      boxplotHTML = pio.to_html(fig,
                                default_width='500px', default_height='500px', \
                                full_html=False)
    except:
      boxplotHTML = "  <p>A boxplot should be here, but there was a problem with plotly.</p>"

    HTMLTextLines = []

    HTMLTextLines.append('<html>')
    HTMLTextLines.append('<head>')
    HTMLTextLines.append('  <title>EvoPIE Data Analysis Dashboard</title>')
    HTMLTextLines.append('</head>')
    HTMLTextLines.append('')
    HTMLTextLines.append('<body>')
    HTMLTextLines.append('  <h1>EvoPIE Data Analysis Dashboard</h1>')

    # Here I'm just using the HTML page to see how to access the quizzes DB
    HTMLTextLines.append('  <p>Here is a dump of the Quiz model from the DB:</p>')
    HTMLTextLines.append('  <samp>')
    myQuiz = models.Quiz()
    HTMLTextLines.append( str(myQuiz.dump_as_dict()) )
    HTMLTextLines.append('  </samp>')

    # Integrate with Plot.ly?
    HTMLTextLines.append('<br><br><hr><br><br>')
    HTMLTextLines.append('  <p>Here is a silly data visualization example with nothing to do with our data:</p>')
    HTMLTextLines.append(boxplotHTML)
    HTMLTextLines.append('</body>')
    HTMLTextLines.append('</html>')

    return os.linesep.join(HTMLTextLines)
