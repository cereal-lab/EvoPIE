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
