import numpy as np
import pandas as pd
import scipy.stats as stats

from datalayer import LOGGER


# Reminder of the columns of the standard dataframe we will
# get for test results
#    pd.DataFrame({'StudentID':StudentIDs, \
#                  'QuestionID':QuestionIDs, \
#                  'InitialScore':InitialScores, \
#                  'RevisedScore':RevisedScores})


def getOverallScoresStats(dataset, whichScore, excludeQuestionSet=set()):
  """
  Return the mean, standard deviation, and sample size of the specified
  quiz.  You may also exclude questions from the computation if you like
  by passing a set of question IDs; however, by default no questions are
  excluded.  You must specify which type of score you are analyzing:
    InitialScore or RevisedScore (as strings with those names).
  """
  quizScores = dataset[ ~dataset.QuestionID.isin(excludeQuestionSet) ] [whichScore]
  return (np.mean(quizScores), np.std(quizScores), len(quizScores))


def splitQuizByQuestionResponse(dataset, whichScore, questionID, threshold=1):
  """
  Take a dataset and return two subsets based on student responses to a 
  specified question.  The first set is comprised of the students who got
  that question incorrect, the second of students who got that question correct.
  Here "correct" is determined by whether the specified score is at least
  the specified threshold value.  By default, to be "correct", you must get 
  a perfect score on the question (1.0).
  """
  allStudents = set(dataset.StudentID)

  # Figure out which students got the question wrong and which got them right
  dfTemp = dataset[ (dataset.QuestionID==questionID) & (dataset[whichScore]<threshold) ]   
  studentsWhoGotQuestionWrong = set(dfTemp.StudentID)
  studentsWhoGotQuestionRight = allStudents - studentsWhoGotQuestionWrong

  # Separate the data based on the students who got the question right or wrong
  df0 = dataset[ dataset.StudentID.isin(studentsWhoGotQuestionWrong) ]
  df1 = dataset[ dataset.StudentID.isin(studentsWhoGotQuestionRight) ]

  return df0, df1
  


def splitQuizByStudentResponse(dataset, whichScore, studentID, threshold=1):
  """
  Take a dataset and return two subsets based on student responses to a 
  specified question.  The first set is comprised of the questions this student got 
  incorrect, the second of questions this student correct.
  Here "correct" is determined by whether the specified score is at least
  the specified threshold value.  By default, to be "correct", you must get 
  a perfect score on the question (1.0).
  """
  allQuestions = set(dataset.QuestionID)

  # Figure out which students got the question wrong and which got them right
  dfTemp = dataset[ (dataset.StudentID==studentID) & (dataset[whichScore]<threshold) ]   
  questionsStudentGotWrong = set(dfTemp.QuestionID)
  questionsStudentGotRight = allQuestions - questionsStudentGotWrong

  # Separate the data based on the students who got the question right or wrong
  df0 = dataset[ dataset.QuestionID.isin(questionsStudentGotWrong) ]
  df1 = dataset[ dataset.QuestionID.isin(questionsStudentGotRight) ]

  return df0, df1


def analyzeSingleQuestion(dataset, whichScore, questionID, excludeQuestion=True):
  """
  Compute the item descrimination value for a single question by estimating the
  point-biserial correlation coefficient.  Also compute it's test statistic.
  Return both of these values, in that order.  You can either exclude or not
  exclude the question under consideration fro the mean calculations of the 
  split datasets.  It makes more sense to exclude them, so that is the default.
  """
  df0, df1 = splitQuizByQuestionResponse(dataset, whichScore, questionID, 1)

  excludeSet = set()
  if excludeQuestion:
      excludeSet.add(questionID)

  xb, sn, n = getOverallScoresStats(dataset, whichScore, excludeSet)
  m0, s0, n0 = getOverallScoresStats(df0, whichScore, excludeSet)
  m1, s1, n1 = getOverallScoresStats(df1, whichScore, excludeSet)

  scalar = np.sqrt(n1*n0/n**2)
  itemDiscrimationIndex = ((m1 - m0) / sn) * scalar
  ttestStat = itemDiscrimationIndex * np.sqrt(n-2) / np.sqrt(1 - itemDiscrimationIndex)

  return itemDiscrimationIndex, ttestStat



def analyzeSingleStudent(dataset, whichScore, studentID, excludeStudent=True):
  """
  Compute the item descrimination value for a single student by estimating the
  point-biserial correlation coefficient.  Also compute it's test statistic.
  Return both of these values, in that order.  You can either exclude or not
  exclude the student under consideration fro the mean calculations of the 
  split datasets.  It makes more sense to exclude them, so that is the default.
  """
  df0, df1 = splitQuizByStudentResponse(dataset, whichScore, studentID, 1)

  excludeSet = set()
  if excludeStudent:
      excludeSet.add(studentID)

  xb, sn, n = getOverallScoresStats(dataset, whichScore, excludeSet)
  m0, s0, n0 = getOverallScoresStats(df0, whichScore, excludeSet)
  m1, s1, n1 = getOverallScoresStats(df1, whichScore, excludeSet)

  scalar = np.sqrt(n1*n0/n**2)
  itemDiscrimationIndex = ((m1 - m0) / sn) * scalar
  ttestStat = itemDiscrimationIndex * np.sqrt(n-2) / np.sqrt(1 - itemDiscrimationIndex)

  return itemDiscrimationIndex, ttestStat


def analyzeQuestions(dataset, whichScores, contextDict):
  """
  Conduct the item discrimination analysis for the scores of a particular
  question.  Return a Pandas dataframe that has the point-biserial correlation
  coefficient (item discriminiation score) for every question, as well as a test
  statistic that can be compared to a one-tailed student-t distribution.  You 
  may choose to exclude each question from its own mean calculations for the
  statistic if you like.  Since this makes the most sense, it is the default.
  """
  questionIDs = set(dataset.QuestionID)

  QuestionIDs       = pd.Series([], dtype='int')
  DiscriminationIdx = pd.Series([], dtype='float')
  Significance      = pd.Series([], dtype='category')

  ttestCriticalValue = stats.t.ppf(0.95, len(questionIDs))

  # You probably want to exclude each question from its own analysis
  excludeItem = True
  try:
    excludeItem = contextDict["excludeItem"]
  except:
    pass

  # Initialize the data frame
  QuestionIDs       = pd.Series([], dtype='int')
  DiscriminationIdx = pd.Series([], dtype='float')
  Significance      = pd.Series([], dtype='category')

  df = pd.DataFrame({'QuestionID':QuestionIDs, \
                     'DiscriminationIdx':DiscriminationIdx, \
                     'Significance':Significance})  

  # Don't bother ids'ing if there's not enough data
  if (len(set(dataset.StudentID)) < 2) or (len(set(dataset.QuestionID)) < 2):
    LOGGER.warn("There aren't enough questions to compute item descrimination")

  # Otherwise, let's compute the IDS score for each question
  else:
    for pid in questionIDs:
      # Calculate the point-biserial coefficient (and test statistic)
      itemDiscriminationIndex, ttestState =  analyzeSingleQuestion(dataset, whichScores, pid, excludeItem)
      signifFlag = "NOTSIGNIFICANT"
      if ttestState > ttestCriticalValue:
          signifFlag = "SIGNIFICANT"

      # Append these to a new dataset
      QuestionIDs       = pd.Series([pid], dtype='int')
      DiscriminationIdx = pd.Series([itemDiscriminationIndex], dtype='float')
      Significance      = pd.Series([signifFlag], dtype='category')

      # Assemble these into a new row, then add it to the data frame
      dfNewRow = pd.DataFrame({'QuestionID':QuestionIDs, \
                               'DiscriminationIdx':DiscriminationIdx, \
                               'Significance':Significance})

      df = pd.concat([df, dfNewRow])  

  return df


def analyzeStudents(dataset, whichScores, contextDict):
  """
  Conduct the item discrimination analysis for the scores of a particular
  student.  Return a Pandas dataframe that has the point-biserial correlation
  coefficient (item discriminiation score) for every student, as well as a test
  statistic that can be compared to a one-tailed student-t distribution.  You 
  may choose to exclude each question from its own mean calculations for the
  statistic if you like.  Since this makes the most sense, it is the default.
  """
  studentIDs = set(dataset.StudentID)

  StudentIDs       = pd.Series([], dtype='int')
  DiscriminationIdx = pd.Series([], dtype='float')
  Significance      = pd.Series([], dtype='category')

  ttestCriticalValue = stats.t.ppf(0.95, len(studentIDs))

  # You probably want to exclude each student from its own analysis
  excludeItem = True
  try:
    excludeItem = contextDict["excludeItem"]
  except:
    pass

  # Initialize the data frame
  StudentIDs        = pd.Series([], dtype='int')
  DiscriminationIdx = pd.Series([], dtype='float')
  Significance      = pd.Series([], dtype='category')

  df = pd.DataFrame({'StudentID':StudentIDs, \
                     'DiscriminationIdx':DiscriminationIdx, \
                     'Significance':Significance})  

  # Don't bother ids'ing if there's not enough data
  if (len(set(dataset.StudentID)) < 2) or (len(set(dataset.QuestionID)) < 2):
    LOGGER.warn("There aren't enough students or questions to compute item descrimination")

  # Otherwise, let's compute the IDS score for each question
  else:
    for sid in studentIDs:
      # Calculate the point-biserial coefficient (and test statistic)
      itemDiscriminationIndex, ttestState =  analyzeSingleStudent(dataset, whichScores, sid, excludeItem)
      signifFlag = "NOTSIGNIFICANT"
      if ttestState > ttestCriticalValue:
          signifFlag = "SIGNIFICANT"

      # Append these to a new dataset
      StudentIDs        = pd.Series([sid], dtype='int')
      DiscriminationIdx = pd.Series([itemDiscriminationIndex], dtype='float')
      Significance      = pd.Series([signifFlag], dtype='category')

      # Now assemble the series into a row to add, then add it to the data frame
      dfNewRow = pd.DataFrame({'StudentID':StudentIDs, \
                               'DiscriminationIdx':DiscriminationIdx, \
                               'Significance':Significance})
      df = pd.concat([df, dfNewRow])  

  return df


