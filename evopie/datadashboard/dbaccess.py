# pylint: disable=no-member
# pylint: disable=E1101

# This module is meant to provide a database access layer for the data
# analytics dashboard.

import os, sys

from evopie import models, APP, DB # get also DB from there

import sqlalchemy

import numpy as np
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
  quizList = None

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
  quizAttemptList = None

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
  questionList = None

  try:
    quiz = models.Quiz.query.get_or_404(quizID)
    questionList = [question.dump_as_dict() for question in quiz.quiz_questions]
  except Exception as error:
    if (showError):
      questionList = ["DB Error: " + str(error)]

  return questionList


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
