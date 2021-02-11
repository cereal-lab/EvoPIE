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
