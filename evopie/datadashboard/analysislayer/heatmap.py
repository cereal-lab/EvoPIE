
import pandas as pd

def getStudentScores(df, whichScore):
    # Get all unique student IDs
    students = set(df['StudentID'].unique())
    
    # Compute the number of questions each student got correct
    scoresSum = {}
    for sid in students:
      scoresSum[sid] = sum(df[df['StudentID'] == sid][whichScore])

    return scoresSum


def getQuestionScores(df, whichScore):
    # Get all unique question IDs
    questions = set(df['QuestionID'].unique())
    
    # Compute the number of students that got each question wrong
    scoresSum = {}
    for qid in questions:
      scoresSum[qid] = sum(1.0 - df[df['QuestionID'] == qid][whichScore])

    return scoresSum


def appendAndSortStudentScorestoDataSet(df, scoresSum):
    df['TotalScores'] = [0.0] * df.shape[0]
    #TotalStudentScores = pd.Series([], dtype='float')

    colIdx = df.columns.get_loc('TotalScores')
    for rowIdx in range(df.shape[0]):
        sid = df.iloc[rowIdx]['StudentID']
        if (scoresSum[sid] > 0):
          df.iat[rowIdx, colIdx] = scoresSum[sid]

    df.sort_values('TotalScores', ascending=False, inplace=True)


def appendAndSortQuestionScorestoDataSet(df, scoresSum):
    df['TotalScores'] = [0.0] * df.shape[0]

    colIdx = df.columns.get_loc('TotalScores')
    for rowIdx in range(df.shape[0]):
        qid = df.iloc[rowIdx]['QuestionID']
        if (scoresSum[qid] > 0):
          df.iat[rowIdx, colIdx] = scoresSum[qid]

    df.sort_values('TotalScores', ascending=False, inplace=True)


def cleanUpQuestionDF(dataset, whichScores):
  """
  We want the heatmap data frame to be capable of indicating whether student
  pre- and post-quiz results *changed*.  This routine changes the 0/1 scores
  for both the initial and revised scores to scores between 0 and 3.  For the
  initial scores, 0 means "wrong" and 3 means "right".  For the revised, 0
  means wrong both times, 1 means it was right then wrong in post, 2 means
  the reverse, and 3 means got it right both times.
  """
  df = dataset.copy()

  if whichScores == 'RevisedScore':
    for index in range(df.shape[0]):
      oldAnswer = df.iloc[index]['InitialScore']
      newAnswer = df.iloc[index]['RevisedScore']
 
      # If it's wrong in both places, leave it a zero
      if (oldAnswer == 0) and (newAnswer == 0):
        df.iloc[index, df.columns.get_loc('RevisedScore')] = 0.0

      # If it *was* right, but now is wrong, make it a 1
      elif (oldAnswer > 0) and (newAnswer == 0):
        df.iloc[index, df.columns.get_loc('RevisedScore')] = 1.0

      # If it *was* wrong, but now is right, make it a 2
      elif (oldAnswer == 0) and (newAnswer > 0):
        df.iloc[index, df.columns.get_loc('RevisedScore')] = 2.0

      # If it is right both times, make it as 3
      elif (oldAnswer > 0) and (newAnswer > 0):
        df.iloc[index, df.columns.get_loc('RevisedScore')] = 3.0

  else:
    for index in range(df.shape[0]):
      # Match right initially to 3.0 (right both times)
      if (df.iloc[index]['InitialScore'] > 0.0):
        df.iloc[index, df.columns.get_loc('InitialScore')] = 3.0
      else:
        df.iloc[index, df.columns.get_loc('InitialScore')] = 0.0

  return df


def analyzeQuestions(dataset, whichScores, contextDict, quiet=False):
  """
  This function provides a heatmap analysis of a dataset.  It first conducts MDS, then
  performs a clustering in the 2D space.  This is a clustering of questions.  
  """
  scoresSums = None
  try:
    scoresSums = contextDict["scoresSums"]
  except:
    scoresSums = None

  if scoresSums == None:
    scoresSums = getStudentScores(dataset, whichScores)

  appendAndSortStudentScorestoDataSet(dataset, scoresSums)
  df = cleanUpQuestionDF(dataset, whichScores)

  contextDict['studentOrder'] = list(set(df['StudentID']))
  contextDict['questionOrder'] = list(set(df['QuestionID']))

  return df


def analyzeStudents(dataset, whichScores, contextDict, quiet=False):
  """
  This function provides a heatmap analysis of a dataset.  It first conducts MDS, then
  performs a clustering in the 2D space.   This is a clustering of students.
  """
  scoresSums = None
  try:
    scoresSums = contextDict["scoresSums"]
  except:
    scoresSums = None

  if scoresSums == None:
    scoresSums = getQuestionScores(dataset, whichScores)

  appendAndSortQuestionScorestoDataSet(dataset, scoresSums)
  df = cleanUpQuestionDF(dataset, whichScores)

  contextDict['studentOrder'] = list(set(df['StudentID']))
  contextDict['questionOrder'] = list(set(df['QuestionID']))

  return df
