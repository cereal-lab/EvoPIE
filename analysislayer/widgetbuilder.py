import traceback
import pandas as pd
import traceback

from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

import datalayer.dbaccess as da
import analysislayer.plotter as plotter
import analysislayer.utils as dataUtils

import threading
from datalayer import LOGGER

## Change this if you add a measure.
gPlotterDictionary = {"deca":plotter.GenerateDimensionGraph,
                      "hm":plotter.GenerateHeatMap,
                      "mds":plotter.GenerateClusterScatterPlot,
                      "ids":plotter.GenerateItemDescriminationBarPlot,
                      "trad":plotter.GenerateTraditionalDifficultyBarPlot}

class WidgetBuilder(threading.Thread):
  """
  This class is responsible for building the graph widgets.  The interface calls this 
  class to get the right graph, and it handles populating them.  This class is threaded
  and it will start running the thread the first time the PopulateGraphs() method is
  called.  That thread continuously looks for changes and re-generates graphs when
  there are changes.  The widget table is a dictionary, where the key is the type
  of analysis, the view, and the score.  The value is the graph object, as well as
  the quizID that was used to generate that graph.
  """
  def __init__(self):
      self.widgetTable = {}
      self.analysisContextTable = {}
      self.currentQuizID = -1   # Current quiz ID used to build the table
      self.currentQuizDF = None # Current quiz data frame used to build the table
      self.running = False      # Whether or not the thread is running
      self.InitGraphsWithSimpleMessage("No graph selected")
      LOGGER.warn("Created a WidgetBuilder.  There should not be more than one -- so if this messages appears more than once, there is a problem.")


  def GetGraph(self, whichAnalysis, whichView, whichScore):
    """
    Go get the widget for the specified graph out of the widget table and return it.
    If it's not there, return an HTML paragraph as an error message.
    """
    graphObject = None
    contextDict = dict()

    # Only get the graph for the layout if the user is authenticated
    if da.IsValidDashboardUser():
      try:
        graphObject, quizID = self.widgetTable[(whichAnalysis, whichView, whichScore)]
        contextDict = self.analysisContextTable[(whichAnalysis, whichView)]
      except:
        graphObject = html.P(children="Select an analysis", className="graph-component-message")

    # If the user is not authenticated, tell them that instead of showing the plot
    else:
      graphObject = html.P(children="Not a valid user.", className="graph-component-message")
      
    return graphObject, contextDict



  def PutGraph(self, inQuizID, quizDF, whichAnalysis, whichView, whichScore, contextDict):
    """
    Build the graph if it isn't already built and put it in the widget table.
    We check to see if it is already there by verifying that the quiz ID is the same.
    Return whether or not the graph had to be regenerated (updated) or not.
    """
    graphObject = None
    updated = False
    oldQuizID = -1
    contextDict = dict()

    try:
      graphObject, oldQuizID  = self.widgetTable[(whichAnalysis, whichView, whichScore)]
      contextDict = self.analysisContextTable[(whichAnalysis, whichView)]
    except:
      graphObject = None

    # If we already have an object with this quiz ID, no need to re-build it.
    if not oldQuizID == inQuizID:
      LOGGER.info("    Generating graph for quiz", inQuizID, " (v", oldQuizID, "):: ", whichAnalysis, whichView, whichScore)
      graphObject = html.P(children="Unable to build this graph due to an unforseen error", className="graph-component-message")        

      #if (whichAnalysis == "trad"):
      #  print("\n\nDBG:  in the putgaph\n\n", self.currentQuizDF )

      try:
        pltgen = gPlotterDictionary[whichAnalysis] # Get the right plotting routine
        graphObject = pltgen(quizDF, whichScore, inQuizID, whichView, contextDict)  # Generate the graph
      except Exception as err:
        LOGGER.error("     --> Failure in widgetbuilder PutGraph, ", (whichAnalysis, whichView, whichScore))
        LOGGER.error("         Error: ", str(err), traceback.print_exc())

      self.widgetTable[(whichAnalysis, whichView, whichScore)] = (graphObject, inQuizID) # Store the graph & quizID
      self.analysisContextTable[(whichAnalysis, whichView)] = contextDict  # Store the context for the analysis
      updated = True
    return updated


  def InitGraphsWithSimpleMessage(self, messageStr):
    """
    Fill the entire table with widgets that are just message strings (e.g., that the
    graph is loading).  Use -1 as a key for the quizID to ensure that future "PutGraph"
    calls will be forced to replace it.
    """
    for whichAnalysis in list(gPlotterDictionary.keys()): 
      for whichView in ["question", "student"]:
        for whichScore in ["InitialScore", "RevisedScore"]:
          self.widgetTable[ (whichAnalysis, whichView, whichScore)]  = (html.P(children=messageStr, className="graph-component-message"), -1)


  def PrintWidgetTable(self):
    """
    Print the internal width table (mostly for debugging).
    """
    LOGGER.info("Current Widget Table [", len(self.widgetTable), "]:")
    for key in self.widgetTable:
      whichAnalysis, whichView, whichScore = key
      graphObject, quizID = self.widgetTable[key]
      goName = type(graphObject).__name__
      LOGGER.info('  ', whichAnalysis, whichView, whichScore, quizID, goName)


  def IsReloadNeeded(self, quizID, quizDF):
    """
    Determine whether the dataframe must be be reloaded or not.  This occurs if the
    object isn't a Pandas data frame or if the quizID has changed since we tried last.
    """
    return (not quizID == self.currentQuizID) or (not isinstance(quizDF, pd.DataFrame))


  def PopulateGraphs(self, quizID, quizDF):
    """
    Populate all graphs (if needed) for a given quiz.
    """
    # You only need to re-init if the quiz has changed.
    if self.IsReloadNeeded(quizID, quizDF):
      self.currentQuizDF = quizDF
      self.InitGraphsWithSimpleMessage("Loading graphs for quiz " + str(quizID) + " ...")
      self.currentQuizID = quizID


    # Start the thread updating ...
    if not self.running:
      self.run()


  # Overriden method for threading.Thread.  This is what will execute when
  # the thread is started.
  def run(self):
    """
    This routine will run in its own thread.  It tries to keep the graphs 
    constantly updated.  The PutGraph method is smart enough not to re-build
    the graph if it's already present.  So this routine should just cycle
    until the currentQuizID changes.
    """
    self.running = True
    print("Thread started running...")

    while self.running:
      for whichAnalysis in list(gPlotterDictionary.keys()): 
        for whichView in ["question", "student"]:
          for whichScore in ["InitialScore", "RevisedScore"]:  # Change the body if you add a measure
            contextDict = dict()
            self.PutGraph(self.currentQuizID, self.currentQuizDF, whichAnalysis, whichView, whichScore, contextDict)


    self.running = False    


  def GetQuestionDetailHeader(self, quizDetailDF, questionID, whichScores):
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
  

  def GetQuestionDetailsGraph(self, quizDetailDF, questionID, whichScores):
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


  def GetStudentDetailsGraph(self, quizID, studentID, quizDetailDF):
    """
    Given a quiz ID and a question ID, populate the build the plot for the question detail
    """
    detailsPlot = None

    try:
      if self.IsReloadNeeded(quizID, quizDetailDF):  # Don't reload the data if you already have it ...
        quizDetailDF = da.GetScoresDataframe(quizID) 

      detailsPlot = plotter.GenerateStudentDistributionGraph(quizDetailDF, studentID)
      
    except:
      detailsPlot = html.P(children="Error loading student detail plot", className="graph-component-message")

    return detailsPlot


# Create a global Widget Builder
# This is a singleton object and should *not* be created more than once!
gBuilder = WidgetBuilder()
