import traceback
import pandas as pd
import traceback
import hashlib 
import time
import os
import logging

# Flask/Dash imports
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

# Dashboard imports
import datalayer.models as models
import datalayer.dbaccess as da
from datalayer import LOGGER
import analysislayer.plotter as plotter
import analysislayer.utils as dataUtils

## Change this if you add a measure.
gPlotterDictionary = {"deca":plotter.GenerateDimensionGraph,
                      "hm":plotter.GenerateHeatMap,
                      "mds":plotter.GenerateClusterScatterPlot,
                      "ids":plotter.GenerateItemDescriminationBarPlot,
                      "trad":plotter.GenerateTraditionalDifficultyBarPlot}


def GetGraph(quizID, whichAnalysis, whichView, whichScore):
  """
  Go get the widget for the specified graph out of the widget table and return it.
  If it's not there, return an HTML paragraph as an error message.
  """
  graphObject = None 
  hashCheck = ""
  contextDict = dict()

  # Only get the graph for the layout if the user is authenticated
  if da.IsValidDashboardUser():
    try:
      graphObject, hashCheck, contextDict = da.GetStoredWidgetObject(quizID,whichAnalysis,whichScore,whichView,)
    except:
      graphObject = html.P(children="Graph object not available currently", className="graph-component-message")

  # If the user is not authenticated, tell them that instead of showing the plot
  else:
    graphObject = html.P(children="Not a valid user.", className="graph-component-message")
    
  return graphObject, contextDict



def PutGraph(inQuizID, quizDF, whichAnalysis, whichView, whichScore, contextDict):
  """
  Build the graph if it isn't already built and put it in the widget table.
  We check to see if it is already there by verifying that the quiz ID is the same.
  Return whether or not the graph had to be regenerated (updated) or not.
  """
  graphObject = None
  hashCheck = "NOHASH"
  contextDict = dict()
  updated = False

  try:
    graphObject, hashCheck, contextDict = da.GetStoredWidgetObject(inQuizID,whichAnalysis,whichScore,whichView)
  except:
    pass

  # Get the unique hash string associated with this data frame
  currentHash = hashlib.sha1(pd.util.hash_pandas_object(quizDF).values).hexdigest()

  # Check if the data frame we are about to analyze is different from the one already
  # stored in the widget table
  if not currentHash == hashCheck:
    LOGGER.info("Generating graph for quiz " + str(inQuizID) + "-" + whichAnalysis + "-" + whichView + "-" + whichScore)
    graphObject = html.P(children="Unable to build this graph due to an unforseen error", className="graph-component-message")        

    # Try to build the graph objects
    try:
      pltgen = gPlotterDictionary[whichAnalysis] # Get the right plotting routine
      graphObject = pltgen(quizDF, whichScore, inQuizID, whichView, contextDict)  # Generate the graph
    except Exception as err:
      LOGGER.error("Failure in widgetupdator PutGraph, " +\
            whichAnalysis + "-" + whichView + "-" + whichScore + " ::: " +\
            str(err) + traceback.print_exc())

    # Put the graph object and the context dictionary in the widget table
    da.PutStoredWidgetObject(inQuizID, whichAnalysis, whichScore, whichView, currentHash, graphObject, contextDict)
    updated = True

  return updated


def UpdateTable():
  """
  Spin through all quizzes and try to rebuild all graph objects, if needed
  """
  quizList = da.GetQuizOptionList()

  ## RPW:  This should be done repeatedly ... perhaps with some delay?
  for quiz in quizList:
    # Grab the data for this specific quiz
    quizID = quiz['value']
    currentQuizDF = da.GetScoresDataframe(quizID)

    for whichAnalysis in list(gPlotterDictionary.keys()):
      for whichView in ["question", "student"]:
        for whichScore in ["InitialScore", "RevisedScore"]:
          contextDict = dict()
          PutGraph(quizID, currentQuizDF, whichAnalysis, whichView, whichScore, contextDict)
  

def GetQuestionDetailHeader(quizDetailDF, questionID, whichScores):
  """
  Given a quiz ID and a question ID, generate the header for current plot
  """
  toolTip = None

  try:
    questionText = quizDetailDF['QuestionText'][0]
    toolTip = html.Div(
        [
            html.H1(
                [
                    html.Span(
                        dataUtils.StripHTMLMarkers(questionText, 40),
                        id="tooltip-target", 
                    ),
                ],
                className="tooltip-header"
            ),
            dbc.Tooltip(
                questionText,
                target="tooltip-target",
            ),
        ]
    )

  except:
    toolTip = html.H1(children="Error loading header", className="graph-component-message")
    traceback.print_exc()

  return toolTip
  

def GetQuestionDetailsGraph(quizDetailDF, questionID, whichScores):
  """
  Given a quiz ID and a question ID, populate the build the plot for the question detail
  """
  detailsPlot = None

  try:
    detailsPlot = plotter.GenerateQuestionDetailPlot(quizDetailDF, questionID, whichScores)

  except:
    detailsPlot = html.P(children="Error loading questions detail plot", className="graph-component-message")
    traceback.print_exc()

  return detailsPlot


def GetStudentDetailsGraph(quizID, studentID, quizDetailDF):
  """
  Given a quiz ID and a question ID, populate the build the plot for the question detail
  """
  detailsPlot = None

  try:
    quizDetailDF = da.GetScoresDataframe(quizID) 
    detailsPlot = plotter.GenerateStudentDistributionGraph(quizDetailDF, studentID)
    
  except:
    detailsPlot = html.P(children="Error loading student detail plot", className="graph-component-message")

  return detailsPlot


# If this is run as a stand-along program, it should loop indefinitely, rebuilding
# graphs for the widget table when needed ad infnitum.
#if __name__ == '__main__':
def StartUpdater(sleepTimeInSeconds):
  LOGGER.info("The widget updater process is starting up.")

  status = True
  models.DB.create_all() # Make sure all the tables exist

  while (status):
    UpdateTable()
    if (sleepTimeInSeconds < 0):
      status = False
    else:
      time.sleep(sleepTimeInSeconds)  # Wait a little bit of time so we aren't slamming the DB over and over again

  LOGGER.info("The widget updator process is closing down.")
