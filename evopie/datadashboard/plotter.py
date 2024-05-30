from dash import dcc
from dash import html
import dash_cytoscape as cyto
import pandas as pd
import numpy as np
import sys

import evopie.datadashboard.utils as dataUtils

import evopie.datadashboard.analysislayer.heatmap as heatmap
import evopie.datadashboard.analysislayer.deca as deca
import evopie.datadashboard.analysislayer.itemdiscrim as itemdescrim
import evopie.datadashboard.analysislayer.cluster as cluster
import evopie.datadashboard.analysislayer.traditional as traditional
import evopie.datadashboard.analysislayer.distribution as dist

try:
  import plotly.express as px
  import plotly.io as pio
  import plotly.graph_objects as go
  import plotly.figure_factory as ff
except:
  pass


def GenerateQuestionDetailPlot(df, questionID=0, whichScores='InitialScores', contextDict=dict()):
    """
    Take a dataframe with information about a particular question and
    produce a bar plot to display these results.  Return that Dash
    component.
    """
    # Extract the data we need
    order = np.argsort(list(df['NumberStudents']))
    xVals = df['ResponseText'][order].tolist()#list(range(1,len(df['NumberStudents'])+1))
    yVals = df['NumberStudents'][order].tolist()
    hoverVals = df['ResponseText'][order].tolist()
    correctVals = df['CorrectResponse'][order].tolist()
    questionText = df['QuestionText'][0]

    # Establish the color palette to highlight the correct answer
    colors = ['lightslategray',] * 5
    for idx in range(len(correctVals)):
      xVals[idx] = dataUtils.StripHTMLMarkers(xVals[idx])  # Truncate the x label string
      if correctVals[idx]:
        colors[idx] = 'crimson'

    # Build the graph and Dash component
    fig = go.Bar(y=xVals,
                 x=yVals,
                 hovertext=hoverVals,
                 marker_color=colors,
                 orientation='h')
    #fig.update_xaxes(type='category', showgrid=False, visible=False)
    #fig.update_yaxes(showgrid=False)

    titleStr = dataUtils.StripHTMLMarkers(whichScores+'-Q' + str(questionID) + ': ' + questionText, 40)

    graph = dcc.Graph(figure={'data': [fig],
                              'layout':go.Layout(title=titleStr, 
                                                 yaxis =  {'showgrid': False,
                                                          'automargin': True},#, 'visible':False},
                                                 xaxis =  {'showgrid': False},
                                                 barmode="relative")})

    return graph



def GenerateStudentDistributionGraph(df, studentID=0, contextDict=dict()):
  """
  Take a dataframe and run analysis to get each student's average score for initial and revised. 
  The distribution will have 2 entries for each student. Then create a distribution graph that 
  highlights the particualr student that was selected.
  """
  print("trying analyze students, studentID=", studentID)
  resultsDF = dist.analyzeStudents(df, "both", contextDict)
  print(resultsDF)

  # This try block gets the initial and revised average scores for the specific student selected
  try:
    # get the scores for the selected student from the df
    studentInitialScore = resultsDF.loc[(resultsDF['StudentID'] == int(studentID)) & (resultsDF['variable'] == "InitialScore")]
    studentInitialScore = studentInitialScore.iat[0,2]
    studentRevisedScore = resultsDF.loc[(resultsDF['StudentID'] == int(studentID)) & (resultsDF['variable'] == "RevisedScore")]
    studentRevisedScore = studentRevisedScore.iat[0,2]

    # print scores and student ID for debugging
    print("Student ID: ", studentID)
    print("inital score: ", studentInitialScore)
    print("revised score: ", studentRevisedScore)
  except Exception as e:
    print("getting student details did not work", e)


   # This block builds the graph itself, both positional traces for the student, as 
   # well as the overall density plot itself
  resultsDF = resultsDF['value'].to_numpy()
  resultsList = [resultsDF]
  groupLabels = ['Student Average Scores']
  try:
    # create the graph for the distribution without a histogram, with a rug plot
    print("DBG:  1 before distplot")
    graph = ff.create_distplot(resultsList, groupLabels, show_hist=False)
    print("DBG:  2 after distplot")
    graph = ff.create_distplot(resultsList, groupLabels, show_hist=False)

    # adds the trace for the initial score. This shows up on the rug plot.
    posMarkerInitialScore=dict(x=[studentInitialScore],
               y=['Student Average Scores'],
               mode='lines+markers',
               name='Inital Score',
               marker=dict(size=12, color='green', symbol='circle'),
               xaxis= 'x',
               yaxis='y2')

    # adds the trace for the revised score. This shows up on the rug plot.
    posMarkerRevisedScore=dict(x=[studentRevisedScore],
               y=['Student Average Scores'],
               mode='lines+markers',
               name='Revised Score',
               marker=dict(size=12, color='#FF6D19', symbol='circle'),
               xaxis= 'x',
               yaxis='y2')

    ## RPW:  This plotly call is taking a **really long time** ... maybe the lambda expr?
    
    print("DBG:  3 create figure widget", studentInitialScore, studentRevisedScore)    

    # loops through the traces to add in the additional two traces to the plot
    # the graph loading has a latency issue, but I am unaware of how to fix it
    fig = dict(data=[graph.data[k] for k in range(2)]+[posMarkerInitialScore]+[posMarkerRevisedScore],
                      layout=graph.layout)

  except Exception as err:
    print("Plotter Didn't work:", err)

  print("DBG:  4 send it back")    

  # Return the Dash dcc object containing the plotly figure
  return dcc.Graph(id="studentDist", figure=fig)



def GenerateDimensionGraph(df, whichScores, quizID, whichView, contextDict=dict()):
    """
    Take a dataframe with scores, run the DECA analysis, then generate the network graph
    visualization for it and return that Dash component.
    """
    # Run the DECA analysis
    dataset = dataUtils.convertDFToDecaResultsFormat(df, whichScores)
    dims = None
    equivClass = None
    infoHard = set()
    infoEasy = set()
    numItems = 0
    studentEquivalenceClassSize = dict() #initalize empty dict
    nodeLabelPrefix = ""

    # RPW: This needs to change so that the context is passed in/out of the graph generation routine, as well
    contextDict = {"whichScores":whichScores, \
                   "questionSubset":set(), \
                   "doMatrixExtraction":False, \
                   "omitSpanned":False}

    # We need the student analysis, regardless
    studentDims = deca.analyzeStudents(dataset, whichScores, contextDict, True) #this returned 3 objects, so once another object was initalized and given a place to unpack it worked 
    studentEquivClass = contextDict['equivClass']

    if whichView == "question":
      dims = deca.analyzeQuestions(dataset, whichScores, contextDict, True)
      pSet = contextDict['questionSubset']
      equivClass = contextDict['equivClass']
      infoHard, infoEasy = deca.summarizeMaxMinDimensions(studentDims, pSet, studentEquivClass, True)      
      nodeLabelPrefix = "Q"
    else:
      dims = studentDims
      equivClass = studentEquivClass
      nodeLabelPrefix = "S"

    # Build the Dash graph component to sent back
    elementDict = dataUtils.convertDecaQuestionDimsToCytoElementDict(dims, df, whichScores, nodeLabelPrefix) #Asha: added the additional objects in the parameter
    graph =  cyto.Cytoscape(
                id=dataUtils.getGraphComponentName('deca', whichView, whichScores),
                elements = elementDict,
                layout={'name': 'preset'},
                style={'width':'100%', 'height': '400px'},
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)',
                            'width': '15%',
                            'height': '15%',
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'triangle' #arrows pointing at nodes
                        }
                    },
                    {
                        'selector': '.root-deca-node',
                        'style': {'background-color':'black', 'line-color': 'black', 'shape':'diamond'},
                    },
                    {
                        'selector': '.info-hard-node',
                        'style': {'background-color': 'red'}
                    },
                    {
                        'selector': '.info-easy-node',
                        'style': {'background-color': 'green'}
                    }
                ])

    graph.autounselectify = False

    return graph


def ConvertHeatMapDFToMatrixStudentCols(df, questionOrder, studentOrder, whichScores, ticktext):
    """
    This routine produces data structures needed for the plot.ly heatmap figure creator.  It
    preserves the order given and creates hover-over information.  In this case, questions are
    on the x-axis and students are on the y-axis.
    """    
    xList = list(map(str,questionOrder))
    yList = list(map(str,studentOrder))

    # Initialize The Z and hovertext matrices
    zMatrix = []
    hMatrix = []
    for index in range(len(yList)):
      zMatrix.append(['0']*len(xList))
      hMatrix.append([' ']*len(xList))

    for rowIdx, row in df.iterrows():
        # Get the question ID from the dataframe, then look up its index in the ordering list
        questionID = str(int(row['QuestionID']))
        questionIdx = xList.index(questionID)

        # Get the student ID from the dataframe, then look up its index in the ordering list
        studentID  = str(int(row['StudentID']))
        studentIdx = yList.index(studentID)

        # Get the initial or revised score from the dataframe
        score = str(int(row[whichScores]))
        zMatrix[studentIdx][questionIdx] = score

        # Convert the score to meaningful text for the hover-over
        zLabel = ticktext[int(float(score))]
        hMatrix[studentIdx][questionIdx] = 'Question {}<br />Student {}<br />{}'.format(questionID, studentID, zLabel)

    return xList, yList, zMatrix, hMatrix


def ConvertHeatMapDFToMatrixQuestionCols(df, questionOrder, studentOrder, whichScores, ticktext):
    """
    This routine produces data structures needed for the plot.ly heatmap figure creator.  It
    preserves the order given and creates hover-over information.  In this case, students are
    on the x-axis and questions are on the y-axis.
    """
    xList = list(map(str,studentOrder))
    yList = list(map(str,questionOrder))

    # Initialize The Z and hovertext matrices
    zMatrix = []
    hMatrix = []
    for index in range(len(yList)):
      zMatrix.append(['0']*len(xList))
      hMatrix.append([' ']*len(xList))

    for rowIdx, row in df.iterrows():
        # Get the student ID from the dataframe, then look up its index in the ordering list
        studentID  = str(int(row['StudentID']))
        studentIdx = xList.index(studentID)

        # Get the question ID from the dataframe, then look up its index in the ordering list
        questionID = str(int(row['QuestionID']))
        questionIdx = yList.index(questionID)

        # Get the initial or revised score from the dataframe
        score = str(int(row[whichScores]))
        zMatrix[questionIdx][studentIdx] = str(score)

        # Convert the score to meaningful text for the hover-over
        zLabel = ticktext[int(float(score))]
        hMatrix[questionIdx][studentIdx] = 'Student {}<br />Question {}<br />{}'.format(studentID, questionID, zLabel)

    return xList, yList, zMatrix, hMatrix


def GenerateHeatMap(df, whichScores, quizID, whichView, contextDict=dict()):
    plotDataObj = None
    ticktext = ""

    # RPW:  This needs to be handled differently ... passed in and out, etc.
    if "scoresSums" not in contextDict:
      contextDict = {"scoresSums":None}

    # Grab the question data sorted by number of students who got each question right.
    if whichView == "question":
      df = heatmap.analyzeQuestions(df, whichScores, contextDict)

    # Grab the student data sorted by number of questions each student got right.
    else:
      df = heatmap.analyzeStudents(df, whichScores, contextDict)

    studentOrder = contextDict['studentOrder']
    questionOrder = contextDict['questionOrder']

    # If the result is empty, create a message to display
    graph = html.P(children="Insuffient data to create graph.", className="graph-component-message")

    # Otherwise, build the graph object
    if not df.empty:
      xLabel = ""
      yLabel = ""
      xLen = 0
      
      # Setup the captions, legends, and colors
      titleText = "Quiz " + str(quizID)
      tickvals = [0.0, 1.0, 2.0, 3.0]
      ticktext = ['Incorrect', 'Change to Incorrect', 'Changed to Correct', 'Correct']
      dcolorsc = [[0.0/3, '#dddddd'], [0.4999999/3, '#dddddd'],   # [0.0, 0.5) gray  ## Wrong
                  [0.5/3, '#F06575'], [1.4999999/3, '#F06575'],   # (0.5, 1.5) pink  ## Was right, now wrong
                  [1.5/3, '#0062C2'], [2.4999999/3, '#0062C2'],   # (1.5, 2.5) blue  ## Was wrong, now right
                  [2.5/3, '#008200'], [3.0000000/3, '#008200']]   # (2.5, 3.0] green

      # Build a heatmap plotly data object that is students-by-questions
      xList = None
      yList = None
      zMatrix = None
      hMatrix = None
      if whichView == "question":
          xList, yList, zMatrix, hMatrix = ConvertHeatMapDFToMatrixQuestionCols(df, questionOrder, studentOrder, whichScores, ticktext)
      else:
          xList, yList, zMatrix, hMatrix = ConvertHeatMapDFToMatrixStudentCols(df, questionOrder, studentOrder, whichScores, ticktext)

      # Create the DCC graph object, place into figure for display purposes
      hm = go.Heatmap(x=xList, y=yList, z=zMatrix, \
                      colorscale=dcolorsc, \
                      colorbar=dict(thickness=25, tickvals=tickvals, ticktext=ticktext), \
                      hoverinfo='text', text=hMatrix)
      fig = go.Figure(data=[hm], layout=go.Layout(title=go.layout.Title(text=titleText)))
      if whichView == "question":
        fig = fig.update_xaxes(title_text="Students")
        fig = fig.update_yaxes(title_text="Questions")
        #fig.update_layout(yaxis = dict(gridcolor='rgba(0,0,0,0)',
        #                               color='rgba(0,0,0,0)'))
        #fig.update_layout(xaxis = dict(gridcolor='rgba(0,0,0,0)',
        #                               color='rgba(0,0,0,0)'))
      else:
        fig = fig.update_xaxes(title_text="Questions")
        fig = fig.update_yaxes(title_text="Students")
        #fig.update_layout(yaxis = dict(gridcolor='rgba(0,0,0,0)',
        #                               color='rgba(0,0,0,0)'))
        #fig.update_layout(xaxis = dict(gridcolor='rgba(0,0,0,0)',
        #                               color='rgba(0,0,0,0)'))
      graph = dcc.Graph(id=dataUtils.getGraphComponentName('heatmap', whichView, whichScores), figure=fig)

    # Set the DCC graph object wrapper back
    return graph



def GenerateItemDescriminationBarPlot(df, whichScores, quizID, whichView, contextDict):
    """
    Produce a bar plot of item descrimination for each question of a particular quiz.
    """
    resultsDF = None
    keyLookup = None
    titleStr = None
    xLabel = None

    # RPW:  This should be passed in / out with the sort order placed in, etc.
    contextDict["excludeItem"] = True

    ## Question Analysis
    if (whichView == "question"):
      resultsDF = itemdescrim.analyzeQuestions(df, whichScores, contextDict)
      keyLookup = "Question"
      titleStr = "Item Discrimination Index for Each Question"
      xLabel = "Question ID"

    ## Student Analysis
    else:
      resultsDF = itemdescrim.analyzeStudents(df, whichScores, contextDict)
      keyLookup = "Student"
      titleStr = "Item Discrimination Index for Each Student"
      xLabel = "Student ID"

    # If the result is empty, create a message to display
    graph = html.P(children="Insuffient data to create graph.", className="graph-component-message")

    # Otherwise, build the graph object
    if not resultsDF.empty:
      # Decide about the axis ordering based on the descrim value
      tmpVals = np.array(list(resultsDF['DiscriminationIdx']))
      axisOrdering = (-tmpVals).argsort()  # Reverse sort
      if (whichScores.lower()[0:5] == "revis") and ('axisOrdering' in contextDict):
        axisOrdering = contextDict['axisOrdering']
      elif whichScores.lower()[0:5] == "initi":
        contextDict['axisOrdering'] = axisOrdering

      # Extract the data we need & order it 
      valsNumeric = resultsDF[keyLookup+'ID'].iloc[axisOrdering].tolist()
      vals = [keyLookup + ' ' + str(x) for x in valsNumeric]  # Convert to categorical variable
      descrimVals  = resultsDF['DiscriminationIdx'].iloc[axisOrdering].tolist()
      significanceVals = resultsDF['Significance'].iloc[axisOrdering].tolist()

      titleText = "Quiz " + str(quizID)

      # Establish the color palette to highlight the correct answer
      colors = ['lightslategray',] * len(significanceVals)
      for idx in range(len(significanceVals)):
        if significanceVals[idx]:
          colors[idx] = 'crimson'

      # Build the graph and Dash component
      fig = go.Bar(x=vals,
                  y=descrimVals,
                  marker_color=colors,
                  orientation='v')
                  #,
                  #labels=dict(x="Question ID", y="Item Discrimination", color="Significance"))

      graph = dcc.Graph(id=dataUtils.getGraphComponentName('ids', whichView, whichScores),
                        figure={'data': [fig],
                                'layout':go.Layout(title=titleText, 
                                                  xaxis =  {'showgrid': False,
                                                            'categoryorder':'array', #'total descending', 
                                                            'categoryarray':axisOrdering,
                                                            'title':xLabel,
                                                            'automargin': True},
                                                  yaxis =  {'showgrid': True, 
                                                            'range':[-1,1],
                                                            'tick0':np.arange(-1,1,0.25),
                                                            'title':titleStr},
                                                  barmode="relative")})

    return graph



def GenerateClusterScatterPlot(df, whichScores, quizID, whichView, contextDict=dict()):
    """
    Produce a bar plot of item descrimination for each question of a particular quiz.
    """
    resultsDF = None
    keyLookup = None
    titleStr = None

    # RPW:  The context dictionary should be passed in and out from the plotter, as well
    contextDict = {"whichScores":whichScores}
    contextDict = {"maxClusters":6}

    ## Question Analysis
    if (whichView == "question"):
      resultsDF = cluster.analyzeQuestions(df, whichScores, contextDict)
      keyLookup = "Question"
      grphLabel = "Question Cluster"

    ## Student Analysis
    else:
      resultsDF = cluster.analyzeStudents(df, whichScores, contextDict)
      keyLookup = "Student"
      grphLabel = "Student Cluster"

    # If the result is empty, create a message to display
    graph = html.P(children="Insuffient data to create graph.", className="graph-component-message")

    # Otherwise, build the graph object
    if not resultsDF.empty:
      questionText = [keyLookup + ' ' + str(x) for x in resultsDF[keyLookup+'ID']]

      # px.colors.qualitative.Vivid
      titleText = "Quiz " + str(quizID)

      # Establish the color palette to highlight the correct answer
      colors = []
      for clusterVal in resultsDF.Cluster:
          colors.append( px.colors.qualitative.Vivid[clusterVal] )

      # Create the actual scatter plot object
      fig = go.Scatter(x=resultsDF.Cluster, 
                       y=resultsDF.GrpCounter, 
                       mode="markers", 
                       marker_color=colors,
                       text=questionText,
                       marker=dict(size=16))

      graph = dcc.Graph(id=dataUtils.getGraphComponentName('mds', whichView, whichScores),
                        figure={'data': [fig],
                                'layout':go.Layout(title=titleText, 
                                                  #color_discrete_sequence=px.colors.qualitative.Vivid,
                                                  xaxis =  {'showgrid': False, #Asha: removed grid lines
                                                            'title':grphLabel, #Asha: x-axis title changed to correspond with the view (Question & Student)
                                                            'automargin': True,
                                                            'zeroline': False}, #Asha: removed zeroline for a cleaner look
                                                  yaxis =  {'showgrid': False,
                                                            'showticklabels': False,
                                                            'zeroline': False})}) #Asha: removed y-axis label

    return graph


def GenerateTraditionalDifficultyBarPlot(df, whichScores, quizID, whichView, contextDict=dict()):
    """
    Produce a bar plot of item descrimination for each question of a particular quiz.
    """
    resultsDF = None
    keyLookup = None
    titleStr = None
    xLabel = None

    ## Question Analysis
    if (whichView == "question"):
      resultsDF = traditional.analyzeQuestions(df, whichScores, contextDict)
      keyLookup = "Question"
      titleStr = "Ratio of Students Who Missed This"
      xLabel = "Question ID"

    ## Student Analysis
    else:
      resultsDF = traditional.analyzeStudents(df, whichScores, contextDict)
      keyLookup = "Student"
      titleStr = "Ratio of Incorrect Questions by Student"
      xLabel = "Student ID"

    # Decide about the axis ordering based on the descrim value
    tmpVals = np.array(list(resultsDF[whichScores]))
    axisOrdering = (-tmpVals).argsort()  # Sort
    if (whichScores.lower()[0:5] == "revis") and ('axisOrdering' in contextDict):
      axisOrdering = contextDict['axisOrdering']
    elif whichScores.lower()[0:5] == "initi":
      contextDict['axisOrdering'] = axisOrdering 

    tradVals  = resultsDF[whichScores].iloc[axisOrdering].tolist()
    valsNumeric = resultsDF[keyLookup+'ID'].iloc[axisOrdering].tolist()
    vals = [keyLookup + ' ' + str(x) for x in valsNumeric]  # Convert to categorical variable

    titleText = "Quiz " + str(quizID)

    # Establish the color palette to highlight the correct answer
    colors = ['lightslategray',] * len(valsNumeric)

    # Build the graph and Dash component
    fig = go.Bar(x=vals,
                 y=tradVals,
                 marker_color=colors,
                 orientation='v')

    graph = dcc.Graph(id=dataUtils.getGraphComponentName('trad', whichView, whichScores),
                      figure={'data': [fig],
                              'layout':go.Layout(title=titleText, 
                                                xaxis =  {'showgrid': False,
                                                          'categoryorder':'array', #'total descending', 
                                                          'categoryarray':axisOrdering,
                                                          'title':xLabel,
                                                          'automargin': True},
                                                yaxis =  {'showgrid': True, 
                                                          'range':[0,1],
                                                          'tick0':np.arange(0,1,0.2),
                                                          'title':titleStr},
                                                barmode="relative")})

    return graph