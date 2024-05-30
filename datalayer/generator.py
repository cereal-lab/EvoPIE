# pylint: disable=no-member
# pylint: disable=E1101

# This module is meant to provide a database access layer for the data
# analytics dashboard.

import os, sys

import numpy as np
import pandas as pd
import json


def RecurseDataGeneratorStudentBranch(baseStudent, studentList, branching, maxNumberOfStudents):
  """
  This routine recursively generates a list of students by traversing a tree-like
  structure of missed questions.  The point is to try to preserve some structure
  in the data that we can then try to uncover via dimension extraction, etc.
  Each level presents a (random) opportunity to "branch", in each branch students
  get the same questions wrong as the previous student, and miss a random number of
  additional questions.
  """
  # Get the number of correct answers on the baseStudent's test
  numBaseCorrect = len(baseStudent[baseStudent==1])

  # There's no reason to do anything unless the base student has at least
  # one correct answer, but we buffer that here by 1 because we can still
  # get a lot of students who miss everything just becaue of random chance.
  if (numBaseCorrect > 1) and (maxNumberOfStudents < 0 or len(studentList) < maxNumberOfStudents):
    # Pick a random number of branches, then loop that many times
    numBranches = np.random.poisson(lam=branching, size=1)[0]
    for idx in range(numBranches):
      # Select a random number of additional questions missed
      numAdditionalMissed = np.random.poisson(lam=2, size=1)[0] + 1
      numAdditionalMissed = np.min([numAdditionalMissed, numBaseCorrect])

      # Make a copy of the student, the randomly select some questions for
      # them to miss
      y = baseStudent.copy()
      y[np.random.choice(np.where(y==1)[0],numAdditionalMissed,replace=False)] = 0

      # Add the student to the list, then recurse
      studentList.append(y)
      RecurseDataGeneratorStudentBranch(y, studentList, branching, maxNumberOfStudents)


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


def GetScoresDataframe(quizID, numQuestions, branching=2, maxNumStudents=-1):
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
  RecurseDataGeneratorStudentBranch(primaryStudent, studentListTest1, branching, maxNumStudents)

  # Make a new list where students each perform a little better than
  # on their first test.
  studentListTest2 = ArtificialTestCorrection(studentListTest1, 1)

  numStudents, numQuestions = np.shape(studentListTest1)

  for studentID in range(numStudents):
    for questionID in range(numQuestions):
      initialScore = studentListTest1[studentID][questionID]
      revisedScore = studentListTest2[studentID][questionID]

      StudentIDs    = pd.Series([studentID], dtype='int')
      QuestionIDs   = pd.Series([questionID], dtype='int')
      InitialScores = pd.Series([initialScore], dtype='float')
      RevisedScores = pd.Series([revisedScore], dtype='float')      

      dfNewRow = pd.DataFrame({'StudentID':StudentIDs, \
                               'QuestionID':QuestionIDs, \
                               'InitialScore':InitialScores, \
                               'RevisedScore':RevisedScores})    

      df = pd.concat([df, dfNewRow])  

  return df


def GetQuestionDetailDataframe(quizID, questionID, whichScores, quiet=False):
  # Fake question ID info ...
  QuestionID      = pd.Series([1,1,1,1], dtype='int')

  # Fake question text
  questionText = "What is the fastest land animal in the world?"
  QuestionText    = pd.Series([questionText, questionText, questionText, questionText], dtype='string')

  # Fake respones
  ResponseID      = pd.Series([1,2,3,4], dtype='int')
  ResponseText    = pd.Series(["Cheetah",\
                                "Ostrich",\
                              "Sailfish",\
                              "Peregrine Falcon"], dtype='string')

  # Fake results data
  CorrectResponse = pd.Series([True, False, False, False], dtype='bool')
  NumberStudents  = pd.Series(np.random.randint(0,50,4).tolist(), dtype='int')

  # Build a data frame out of all that malarky!
  df = pd.DataFrame({'QuestionID':QuestionID, \
                      'QuestionText':QuestionText, \
                      'ResponseID':ResponseID, \
                      'ResponseText':ResponseText, \
                      'CorrectResponse':CorrectResponse, \
                      'NumberStudents':NumberStudents})

  return df


def GetQuizOptionList():
  """
  Return a list of fictional quizzes to populate the drop-down in the interface for selecting
  a quiz.
  """
  quizOptionList = []

  for idx in range(3):
    labelStr = "Quiz " + str(idx)
    valueStr = str(idx)
    quizOptionList.append( {'label':labelStr, 'value':valueStr} )

  return quizOptionList
