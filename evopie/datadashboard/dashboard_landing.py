# pylint: disable=no-member
# pylint: disable=E1101

import os, sys
import numpy as np

# Ugly and horrible way to ensure this can load ...
# Get the parent directory, add it to the python path explicitly
pathToThisFilesDir = os.path.dirname(os.path.realpath(__file__))
pathPieces = pathToThisFilesDir.split(os.path.sep)
pathToThisFilesParentDir = os.path.sep.join(pathPieces[0:-1])
sys.path.insert(0,pathToThisFilesParentDir)

from evopie import APP

import evopie.datadashboard.dbaccess as dbaccess
import evopie.datadashboard.formatting as formatting
import evopie.datadashboard.plotting as plotting

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

    # Here I'm just using the HTML page to see how to access the quizzes DB
    HTMLTextLines.append('  <p>Here is some DB noodling:</p>')
    HTMLTextLines.append('  <samp>')


    HTMLTextLines.append( "<h2>Information about Quiz 1</h2>" )
    questionList = dbaccess.GetQuizQuestions(1, True)
    for q in questionList:
      HTMLTextLines.append( str(q) + '<br><br>'  )

    HTMLTextLines.append('<br><br><hr><h2>List of Quizes?</h2>')
    quizList = dbaccess.GetQuizList(True);
    for q in quizList:
      HTMLTextLines.append( str(q) + '<br><br>'  )

    HTMLTextLines.append('<br><br><hr><h2>Dump of Attempts for Quiz 1</h2>')
    quizAttemptList = dbaccess.GetAllAttemptsForQuiz(1, True)
    for q in quizAttemptList:
      HTMLTextLines.append( str(q) + '<br><br>'  )

    HTMLTextLines.append('<br><br><hr><h2>Matrix of Initial Attempts of Quiz 1</h2>')
    #df = dbaccess.GetScoresDataframe(1, HTMLTextLines)
    df = dbaccess.GenerateFakeScoresDataframe(10,2)
    initialScores, revisedScores = formatting.ConvertDFToScoresMatrix(df)
    HTMLTextLines.extend( formatting.CreateHTMLTableFromMatrix(initialScores) )

    HTMLTextLines.append('<br><br><hr><h2>Matrix of Revised Attempts of Quiz 1</h2>')
    HTMLTextLines.extend( formatting.CreateHTMLTableFromMatrix(revisedScores) )

    HTMLTextLines.append('  </samp>')

    # Integrate with Plot.ly?
    HTMLTextLines.append('<br><br><hr><br><br>')
    HTMLTextLines.append('  <p>Here is heatmap visualization of the scores matrices:</p>')
    HTMLTextLines.append(plotting.GetSimpleHeatMap(df, 1, 'InitialScore'))
    HTMLTextLines.append(plotting.GetSimpleHeatMap(df, 1, 'RevisedScore'))
    #HTMLTextLines.append('  <p>Here is a silly data visualization example with nothing to do with our data:</p>')
    #HTMLTextLines.append(plotting.GetPrefabricatedExampleBoxPlot())
    HTMLTextLines.append('</body>')
    HTMLTextLines.append('</html>')

    return os.linesep.join(HTMLTextLines)
