# pylint: disable=no-member
# pylint: disable=E1101

# This module is meant to provide a database access layer for the data
# analytics dashboard.

import os, sys

from evopie import models, APP, DB # get also DB from there

import sqlalchemy

import numpy as np
import pandas as pd
import json


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



## RPW:  You need to clean these up by putting them in useful
##       data structures, as well as dealing with exceptions
##       and when data cannot be found, etc.  They are just
##       placeholders for now.  2/11/2021

def GetQuizList(showError=False):
  """
  Return the list of all quizes in the database.
  """
  quizList = []

  try:
    quizList = [quiz.dump_as_dict() for quiz in models.Quiz.query.all()]
  except Exception as error:
    if (showError):
      quizList = ["DB Error: " + str(error)]

  return quizList


def GetAllAttemptsForQuiz(quizID, showError=False):
  """
  Return the list of all attempts for the specified quiz.
  """
  quizAttemptList = []

  try:
    quizAttemptList = [quiz.dump_as_dict() for quiz in models.QuizAttempt.query.filter_by(quiz_id=quizID)]
  except Exception as error:
    if (showError):
      quizAttemptList = ["DB Error: " + str(error)]

  return quizAttemptList


def GetQuizQuestions(quizID, showError=False):
  """
  Return the list of questions for a quiz.
  """
  questionList = []

  try:
    quiz = models.Quiz.query.get_or_404(quizID)
    questionList = [question.dump_as_dict() for question in quiz.quiz_questions]
  except Exception as error:
    if (showError):
      questionList = ["DB Error: " + str(error)]

  return questionList


def GetScoresDataframe(quizID, dbgHtmlObj):
  """
  This function takes a quiz ID and a pandas dataframe containing
  the students-by-question scores of the initial and revised scores
  the students took the quiz.  Each student and question are a
  a separate row in the table.

  The dbgHtmlObj is the list of strings being made to HTML.  It's
  not used here, but is available for debugging, in case needed.
  """
  # Create an empty Pandas data frame
  StudentIDs    = pd.Series([], dtype='int')
  QuestionIDs   = pd.Series([], dtype='int')
  InitialScores = pd.Series([], dtype='float')
  RevisedScores = pd.Series([], dtype='float')

  df = pd.DataFrame({'StudentID':StudentIDs, \
                     'QuestionID':QuestionIDs, \
                     'InitialScore':InitialScores, \
                     'RevisedScore':RevisedScores})

  # Grab all the quiz attempt records for the specivied quiz ID
  # Send back None for the matrices if the quiz was not there
  try:
    quizAttemptList = [quiz.dump_as_dict() for quiz in models.QuizAttempt.query.filter_by(quiz_id=quizID)]
    initialScoresDict = dict()
    revisedScoresDict = dict()

    # Go through all student quiz attempts for this quiz
    # Return None for both matrices if there is any kind of problem
    for attempt in quizAttemptList:
      studentID = attempt['student_id']
      initialScoresDict[studentID] = UnpackJSONDict(attempt['initial_scores'])
      revisedScoresDict[studentID] = UnpackJSONDict(attempt['revised_scores'])

      for questionID in initialScoresDict[studentID].keys():
        initialScore = initialScoresDict[studentID][questionID]
        revisedScore = revisedScoresDict[studentID][questionID]

        StudentIDs    = StudentIDs.append(pd.Series([studentID], dtype='int'))
        QuestionIDs   = QuestionIDs.append(pd.Series([questionID], dtype='int'))
        InitialScores = InitialScores.append(pd.Series([initialScore], dtype='float'))
        RevisedScores = RevisedScores.append(pd.Series([revisedScore], dtype='float'))

    # Now assemble the series into a dataframe
    df = pd.DataFrame({'StudentID':StudentIDs, \
                       'QuestionID':QuestionIDs, \
                       'InitialScore':InitialScores, \
                       'RevisedScore':RevisedScores})

  # Must have been an error somewhere ...
  except Exception as error:
    return dbgHtmlObj.append("<b>DB Error:</b> " + str(error))

  return df



def RecurseDataGeneratorStudentBranch(baseStudent, studentList, branching):
  """
  This routine recursively generates a list of students by traversing a tree-like
  structure of missed questions.  The point is to try to preserve some structure
  in the data that we can then try to uncover via dimension extraction, etc.
  Each level presents a (random) opportunity to "branch", in each branch students
  get the same problems wrong as the previous student, and miss a random number of
  additional problems.
  """
  # Get the number of correct answers on the baseStudent's test
  numBaseCorrect = len(baseStudent[baseStudent==1])

  # There's no reason to do anything unless the base student has at least
  # one correct answer, but we buffer that here by 1 because we can still
  # get a lot of students who miss everything just becaue of random chance.
  if (numBaseCorrect > 1):
    # Pick a random number of branches, then loop that many times
    numBranches = np.random.poisson(lam=branching, size=1)[0]
    for idx in range(numBranches):
      # Select a random number of additional problems missed
      numAdditionalMissed = np.random.poisson(lam=2, size=1)[0] + 1
      numAdditionalMissed = np.min([numAdditionalMissed, numBaseCorrect])

      # Make a copy of the student, the randomly select some questions for
      # them to miss
      y = baseStudent.copy()
      y[np.random.choice(np.where(y==1)[0],numAdditionalMissed,replace=False)] = 0

      # Add the student to the list, then recurse
      studentList.append(y)
      RecurseDataGeneratorStudentBranch(y, studentList, branching)


def ArtificialTestCorrection(studentList, avgCorrectedQuestions=1):
  """
  This routine takes the previous test results and has each student get
  a random number of questions right the second time around.
  """
  newStudentList = []
  for student in studentList:
    newStudent = student.copy()

    # Correct a random number of missed questions
    missedQuestionIdx = np.where(newStudent==0)[0]
    if len(missedQuestionIdx) > 1:
      numAdditionalCorrected = np.random.poisson(lam=avgCorrectedQuestions-1, size=1)[0] + 1
      numAdditionalCorrected = np.min([numAdditionalCorrected, len(missedQuestionIdx)])
      missedQuestions = np.random.choice(missedQuestionIdx, numAdditionalCorrected, replace=False)
      newStudent[missedQuestions] = 1

    # Add the student to the list
    newStudentList.append(newStudent)

  return newStudentList


def GenerateFakeScoresDataframe(numQuestions, branching=2):
  """
  This function builds a Pandas dataframe with quasi-realistic simulated
  pre- and -post test results.  The parameters are the number of questions
  and a branching factor that will dictate how wide or narrow the tree of
  student performance data will be.  The number of students is implicitly
  determined by the random generating procedure.  The goal is to produce
  a data set that has some structure with respect to what students get
  right or wrong.
  """
  # Create an empty Pandas data frame
  StudentIDs    = pd.Series([], dtype='int')
  QuestionIDs   = pd.Series([], dtype='int')
  InitialScores = pd.Series([], dtype='float')
  RevisedScores = pd.Series([], dtype='float')

  df = pd.DataFrame({'StudentID':StudentIDs, \
                     'QuestionID':QuestionIDs, \
                     'InitialScore':InitialScores, \
                     'RevisedScore':RevisedScores})

  # Make a list of student performances for the first test
  primaryStudent = np.array([1] * numQuestions)
  studentListTest1 = [ primaryStudent ]
  RecurseDataGeneratorStudentBranch(primaryStudent, studentListTest1, branching)

  # Make a new list where students each perform a little better than
  # on their first test.
  studentListTest2 = ArtificialTestCorrection(studentListTest1, 1)

  numStudents, numQuestions = np.shape(studentListTest1)

  for studentID in range(numStudents):
    for questionID in range(numQuestions):
      initialScore = studentListTest1[studentID][questionID]
      revisedScore = studentListTest2[studentID][questionID]

      StudentIDs    = StudentIDs.append(pd.Series([studentID], dtype='int'))
      QuestionIDs   = QuestionIDs.append(pd.Series([questionID], dtype='int'))
      InitialScores = InitialScores.append(pd.Series([initialScore], dtype='float'))
      RevisedScores = RevisedScores.append(pd.Series([revisedScore], dtype='float'))

  # Now assemble the series into a dataframe and return it
  df = pd.DataFrame({'StudentID':StudentIDs, \
                     'QuestionID':QuestionIDs, \
                     'InitialScore':InitialScores, \
                     'RevisedScore':RevisedScores})
  return df
