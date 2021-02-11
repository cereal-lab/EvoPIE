# pylint: disable=no-member
# pylint: disable=E1101

# This module is meant to provide tools to help format data for the dashboard.

import os, sys
import numpy as np

#from evopie import models, APP, DB # get also DB from there




def CreateHTMLTableFromMatrix(matrix):
  """
  This function takes a numpy matrix and builds a list of
  strings that implements an HTML table for that matrix
  """
  # Get the dimensions of the matrix
  numRows, numCols = np.shape(matrix)

  HTMLLines = []
  #HTMLLines.append( "Shape: " + str(numRows) + ", " + str(numCols) + "<br>")
  HTMLLines.append( '<table style="border: 1px solid black">')

  for row in range(numRows):
    HTMLLines.append( '  <tr style="border: 1px solid black"> ')
    for col in range(numCols):
      HTMLLines.append( '  <td style="border: 1px solid black"> ' + str(matrix[row][col]) + "</td>")
    HTMLLines.append( "  </tr>")

  HTMLLines.append( "</table>")

  return HTMLLines



def ConvertDFToScoresMatrix(df):
  """
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
  # Grab all the quiz attempt records for the specified quiz ID
  # as a Pandas data frame.
  #df = GetScoresDataframe(quizID, dbgHtmlObj)

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
