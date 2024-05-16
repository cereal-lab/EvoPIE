import re
import numpy as np
import pandas as pd

import evopie.datadashboard.datalayer.generator as da

gFakeScoresDF=None
import evopie.datadashboard.analysislayer.deca as deca 


def convertDFToScoresMatrix(df):
  """
  RPW:  This may be deprecated ... putting it here to get it out of generator...

  This function takes dataframe representing quiz results
  and returns two numpy matrices.  The first is the matrix of
  students-by-question scores of the initial time the students
  took the quiz.  The second is the matrix of the revised quiz
  attempt.  These matrices are arranged such that students rows
  and questions are columns.  The row and column index should be
  consistent between them.  That is:  row 1 is the same student
  in both matrices (and likewise with questions and columns).

  The dbgHtmlObj is the list of strings being made to HTML.  It's
  not used here, but is available for debugging, in case needed.
  """
  # Initialize the scores dictionaries and quiestion and student ID sets
  questionIDSet = set(df['QuestionID'])
  studentIDSet = set(df['StudentID'])

  # Initialize the scores matrices with zeros of the correct size
  initialScoresMatrix = np.zeros( (len(studentIDSet), len(questionIDSet)))
  revisedScoresMatrix = np.zeros( (len(studentIDSet), len(questionIDSet)))

  # Populate the scores matrices
  sdx = 0
  for student in studentIDSet:
    qdx = 0
    for question in questionIDSet:
      # Filter out only the rows with this student and question IDs
      filteredDF = df[ (df.StudentID == student) & (df.QuestionID == question)]

      # There should only be one such row?  So get the values
      # for each matrix.
      initialScoresMatrix[sdx,qdx] = filteredDF.InitialScore.values[0]
      revisedScoresMatrix[sdx,qdx] = filteredDF.RevisedScore.values[0]

      # Increment question counter
      qdx += 1

    # Increment student counter
    sdx += 1

  return initialScoresMatrix, revisedScoresMatrix


def simpleDifficultyEstimate(dataset, questionList, scoreThreshold=1.0):
  """
  Just count how many students get each question wrong and return that
  as a historgram of counts (one count for each question).
  """
  questionHist = dict()
  for question in questionList:
    questionHist[question] = 0

  for student in dataset:
    for question in questionList:
      try:
        if (dataset[student][question]['score'] < scoreThreshold):
          questionHist[question] += 1
      except:
        pass
        
  return questionHist


def extractMatrixStudentByQuestion(dataset, scoreThreshold=1.0):
  """
  Take a DECA formated results structure and return the Boolean
  matrix indicating which students got which questions.  The matrix
  will be oriented students by questions.
  """
  if len(dataset) > 0:
    sortedStudentList = list(dataset.keys())
    sortedStudentList.sort()
    
    sortedQuestionList = list(dataset[sortedStudentList[0]].keys())
    sortedQuestionList.sort()

    print("DECA-Style Student-by-Question Outcome Matrix:")
    print(str('').ljust(5), end='')
    for question in sortedQuestionList:
      print(str(question).center(5), end='')
    print()

    for student in sortedStudentList:
      if len(set(sortedQuestionList) - set(dataset[student].keys())) > 0:
        continue
        
      print(str(student).ljust(5), end='')
      for question in sortedQuestionList:
        if dataset[student][question]['score'] < scoreThreshold:
          print('0'.center(5), end='')
        else:
          print("1".center(5), end='')
      print()


def extractDominancePairsSet(dims):
  """
  Go through all the dimensions extracted and return a set of 2-tuples such that
  each 2-tuple is a 'dominance pair', that is a list of (id1,id2) such that id1
  strictly dominates id2.
  """
  dominanceSet = set()
  
  for dim in dims:
    n = len(dim)
    for idx in range(n):
      for jdx in range(idx+1,n):
        test1 = dim[idx]
        test2 = dim[jdx]
        dominanceSet.add( (test1[2], test2[2]) )
        
  return dominanceSet


def countDominanceInversions(dominanceSet1, dominanceSet2):
  """
  Count the number of dominance relation pairs in the first set that appear
  inverted in the second set.  That is, count how many times A dominates B
  appears in the second set when B dominates A appears in the first.  This is
  an implicit measure of the quality of the isomorphism between two different
  DECA extractions.
  """
  count = 0  
  for dominancePair in dominanceSet1:
    invertedPair = ( dominancePair[1], dominancePair[0] )
    if invertedPair in dominanceSet2:
      count += 1
  return count


def convertDFToDecaResultsFormat(df, whichScores="InitialScore"):
  """
  Take a pandas data frame in the format as it will come from our 
  EvoPIE database and convert it to the nested dictionary format
  used by DECA.  You can specify whether you want the initial
  score or the revised score.  The initial
  scores are the default.

  The EvoPIE data will be a dataframe where each student-question pair
  is a row in the dataframe, and there are four columns for each 
  observation:  StudentID, QuestionID, InitialScore, RevisedScore.

  The DECA dataset is a dictionary in which the key are student IDs
  and the value is another dictionary.  The student dictionary is one
  in which the key is the question ID and the value is another dictionary.
  The student-question dictionary could contain many things, but it must
  at least contain a key 'score' with a numeric value.
    results[studentID][questionID]['scores']
  """
  # Initilize the DECA results dictionary
  results = {}

  # Spin through each row in the EvoPIE scores data frame
  for rowIdx in range(df.shape[0]):
    # Grab all the necessary data from the row
    studentID = int(df.iloc[rowIdx]['StudentID'])
    questionID = int(df.iloc[rowIdx]['QuestionID'])
    score     = float(df.iloc[rowIdx][whichScores])

    # Insert this data into the results nested dictionaries
    if studentID in results:
      if questionID in results[studentID]:
        results[studentID][questionID]['score'] = score
      else:
        results[studentID][questionID] = {'score':score}
    else:
      results[studentID] = {questionID:{'score':score}}
    
  return results


def convertDecaQuestionDimsToCytoElementDict(dims, df, whichScores, prefix="Q"): #Asha: added df and whichScores in the parameter
  """
  The dash_cytoscape module uses a special dictionary format
  to render graphs.  This function takes the dimensions that
  come out of the question dimension analysis of DECA and
  put them in a form that Cytoscape understands.  It returns
  the structure to place in the "elements" field of the Cytoscape.
  """
  cytoElemDict = []

  dataset = convertDFToDecaResultsFormat(df, whichScores)

  contextDict = {"whichScores":whichScores, \
                   "questionSubset":set(), \
                   "doMatrixExtraction":False, \
                   "omitSpanned":False}

  studentDims = deca.analyzeStudents(dataset, whichScores, contextDict, True)
  studentEquivClass = contextDict['equivClass']
  pSet = contextDict['questionSubset']
  infoHard, infoEasy = deca.summarizeMaxMinDimensions(studentDims, pSet, studentEquivClass, True)

  # The origin of the geometric axes
  cytoElemDict.append({'data':{'id':'root',\
                               'label':''},\
                               'position':{'x':0, 'y':0},\
                               'classes':'root-deca-node'}) # Asha: rearranged curly brackets and corrected a typo; cytoscape selector call in plotter.py now works

  # Add all question/question nodes
  theta = 0
  dTheta = 6.28/float(len(dims))
  for dim in dims:
    radius = 0
    theta = theta + dTheta
    for test in dim:
      radius += 80
      nodeLabel = prefix + str(test[2])
      nodeDict = {'id':str(test[2]),
                  'label':nodeLabel}
      popupDict = {'count':test[1]} # Number of students who got this question wrong
      posDict = {'x': int(radius*np.cos(theta)), 'y': int(radius*np.sin(theta))}
      if test[2] in infoHard:
        cytoElemDict.append({'data':nodeDict,
                            'classes': 'info-hard-node', 
                            'mouseoverNodeData':popupDict,
                            'position':posDict})
      elif test[2] in infoEasy:
        cytoElemDict.append({'data':nodeDict,
                            'classes': 'info-easy-node',
                            'mouseoverNodeData':popupDict,
                            'position':posDict})
      else:
        cytoElemDict.append({'data':nodeDict,
                            'mouseoverNodeData':popupDict,
                            'position':posDict})

  # Add the connections for each dimension
  for dim in dims:
    sourceID = 'root'
    for test in dim:
      destID = str(test[2])
      edgeDict = {'source':sourceID,\
                  'target':destID}
      cytoElemDict.append({'data':edgeDict})
      sourceID = destID 
  
  return cytoElemDict


def convertDataFrameToMatrices(df, whichScores='InitialScore'):
  """
  Convert the scores Pandas data frame into the student-by-question matrices for
  initial and revised scores.  Return those two matrices, as well as the student IDs
  and question IDs, each of which are in row/col order (respectively) for alignment
  witht the matrix positions.
  """
  studentIDs = list(set(df['StudentID']))
  questionIDs = list(set(df['QuestionID']))

  initialMatrix = np.zeros( (len(studentIDs), len(questionIDs)) )
  revisedMatrix = np.zeros( (len(studentIDs), len(questionIDs)) )

  for sidx in range(len(studentIDs)):
    for qidx in range(len(questionIDs)):
      sid = studentIDs[sidx]
      qid = questionIDs[qidx]

      initScore = list(df[ (df.StudentID==sid) & (df.QuestionID==qid) ]['InitialScore'])[0]
      reviScore = list(df[ (df.StudentID==sid) & (df.QuestionID==qid) ]['RevisedScore'])[0]

      initialMatrix[sidx,qidx] = initScore
      revisedMatrix[sidx,qidx] = reviScore

  return initialMatrix, revisedMatrix, studentIDs, questionIDs


def getGraphComponentName(whichGraph, whichAnalysis, whichScores):
  """
  This is a convenience routine that creates a string label in the format that we will
  use in a variety of places too look up a graph component.  This ensures the string is
  always formatted the same way.
  """
  return '-'.join([whichGraph.lower().strip(),
                   whichAnalysis.lower().strip(),
                   whichScores])


def StripHTMLMarkers(x, maxLen=0):
  x = re.sub("</p>", "\n", x)           # Turn end of paragraphs into newlines
  x = re.sub("&lt;/p&gt;", "\n", x)     # Turn end of paragraphs into newlines

  x = re.sub("<br>", "\n", x)           # Turn <br> into newlines
  x = re.sub("&lt;br&gt;", "\n", x)     # Turn <br> into newlines

  x = re.sub(r"&nbsp;", " ", x)         # Turn &nbsp; into an actual space

  x = re.sub(r"&lt;[a-z]+&gt;", "", x)  # Get rid of all other markers
  x = re.sub(r"<[a-z]+>", "", x)        # Get rid of all other markers

  x = re.sub(r"&[a-z]+;", "", x)        # Remove any remaining &.*; 

  # Make sure the string is not bigger than maxLen, as long as maxLen is positive
  x = x.strip()
  if (maxLen > 0) and (len(x) > maxLen):
    x = x[0:(maxLen-3)] + "..."

  return x.strip()

