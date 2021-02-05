# pylint: disable=no-member
# pylint: disable=E1101

from . import models, APP, DB # get also DB from there

import sqlalchemy

import click
import os
import numpy as np
import json

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

def UnpackJSONDict(jsonStr):
  """
  The json.loads command expects dictionaries to use double
  quotes for keys and values that are strings; however, the
  values stored in the database are often single quoted.
  This routine wraps around the json.load and tries to
  work either way.  It returns a dictionary.
  """
  returnDict = dict()

  # Try to directly convert the json string to dictionary
  try:
    returnDict = json.loads(jsonStr)

  # If that fails, swap the single quotes for double quotes
  # and try again
  except json.decoder.JSONDecodeError:
    returnDict = json.loads(jsonStr.replace("'",'"'))

  # Return the result
  return returnDict


def GetScoresMatrix(quizID, dbgHtmlObj):
  """
  This function takes a quiz ID and returns two numpy matrices.
  The first is the matrix of students-by-question scores of the
  initial time the students took the quiz.  The second is the
  matrix of the revised quiz attempt.  These matrices are
  arranged such that students rows and questions are columns.
  The row and column index should be consistent between them.
  That is:  row 1 is the same student in both matrices (and likewise
  with questions and columns).

  The dbgHtmlObj is the list of strings being made to HTML.  It's
  not used here, but is available for debugging, in case needed.
  """
  # Grab all the quiz attempt records for the specivied quiz ID
  # Send back None for the matrices if the quiz was not there
  try:
    quizAttemptList = [quiz.dump_as_dict() for quiz in models.QuizAttempt.query.filter_by(quiz_id=quizID)]
  except:
    return None, None

  # Initialize the scores dictionaries and quiestion and student ID sets
  initialScoresDict = {}
  revisedScoresDict = {}
  questionIDSet = set()
  studentIDSet = set()

  # Go through all student quiz attempts for this quiz
  # Return None for both matrices if there is any kind of problem
  try:
    for attempt in quizAttemptList:
      studentID = attempt['student_id']
      initialScoresDict[studentID] = UnpackJSONDict(attempt['initial_scores'])
      revisedScoresDict[studentID] = UnpackJSONDict(attempt['revised_scores'])

      # Update our sets of question IDs and student IDs
      studentIDSet.add(studentID)
      questionIDSet = questionIDSet.union( set(initialScoresDict[studentID].keys()) )
  except:
    return None, None


  # Initialize the scores matrices with zeros of the correct size
  initialScoresMatrix = np.zeros( (len(studentIDSet), len(questionIDSet)))
  revisedScoresMatrix = np.zeros( (len(studentIDSet), len(questionIDSet)))

  # Populate the scores matrices
  sdx = 0
  for student in studentIDSet:
    qdx = 0
    for question in questionIDSet:
      # Go look up the student and questin in the dictionary,
      # but default to 0 if you can't find it
      try:
        initialScoresMatrix[sdx,qdx] = initialScoresDict[student][question]
        revisedScoresMatrix[sdx,qdx] = revisedScoresDict[student][question]
      except:
        raise

      # Increment question counter
      qdx += 1

    # Increment student counter
    sdx += 1

  return initialScoresMatrix, revisedScoresMatrix


def CreateHTMLTableFromMatrix(matrix):
  """
  This function takes a numpy matrix and builds a list of
  strings that implements an HTML table for that matrix
  """
  # Get the dimensions of the matrix
  numRows, numCols = np.shape(matrix)

  HTMLLines = []
  #HTMLLines.append( "Shape: " + str(numRows) + ", " + str(numCols) + "<br>")
  HTMLLines.append( '<table style="border: 1px solid black">')

  for row in range(numRows):
    HTMLLines.append( '  <tr style="border: 1px solid black"> ')
    for col in range(numCols):
      HTMLLines.append( '  <td style="border: 1px solid black"> ' + str(matrix[row][col]) + "</td>")
    HTMLLines.append( "  </tr>")

  HTMLLines.append( "</table>")

  return HTMLLines


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
    HTMLTextLines.append('  <p>Here is some DB noodling:</p>')
    HTMLTextLines.append('  <samp>')

    try:
      HTMLTextLines.append( "<h2>Information about Quiz 1</h2>" )
      Quiz1 = models.Quiz.query.get_or_404(1)
      HTMLTextLines.append( Quiz1.__doc__.replace('\n', '<br>') )
      questionList = [question.dump_as_dict() for question in Quiz1.quiz_questions]
      for q in questionList:
        HTMLTextLines.append( str(q) + '<br><br>'  )

      HTMLTextLines.append('<br><br><hr><h2>List of Quizes?</h2>')
      quizList = [quiz.dump_as_dict() for quiz in models.Quiz.query.all()]
      for q in quizList:
        HTMLTextLines.append( str(q) + '<br><br>'  )

      HTMLTextLines.append('<br><br><hr><h2>Dump of Attempts for Quiz 1</h2>')
      quizAttemptList = [quiz.dump_as_dict() for quiz in models.QuizAttempt.query.filter_by(quiz_id=1)]
      for q in quizAttemptList:
        HTMLTextLines.append( str(q) + '<br><br>'  )

      HTMLTextLines.append('<br><br><hr><h2>Matrix of Initial Attempts of Quiz 1</h2>')
      initialScores, revisedScores = GetScoresMatrix(1, HTMLTextLines)
      HTMLTextLines.extend( CreateHTMLTableFromMatrix(initialScores) )

      HTMLTextLines.append('<br><br><hr><h2>Matrix of Revised Attempts of Quiz 1</h2>')
      HTMLTextLines.extend( CreateHTMLTableFromMatrix(revisedScores) )
    except Exception as error:
      HTMLTextLines.append("DB Error: " + str(error))

    HTMLTextLines.append('  </samp>')

    # Integrate with Plot.ly?
    HTMLTextLines.append('<br><br><hr><br><br>')
    HTMLTextLines.append('  <p>Here is a silly data visualization example with nothing to do with our data:</p>')
    HTMLTextLines.append(boxplotHTML)
    HTMLTextLines.append('</body>')
    HTMLTextLines.append('</html>')

    return os.linesep.join(HTMLTextLines)
