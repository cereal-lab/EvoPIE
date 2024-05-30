import sys
import numpy as np
import pandas as pd

import evopie.datadashboard.utils as dataUtils


def analyzeQuestions(df, whichScores, contextDict):
  """
  Return a dataframe that has a row for each question on the quiz, and
  a column for the ratio of students who *missed* that question.
  """
  numStudents = len(set(df.StudentID))

  # Compute the ratio of missed questions by aggregating over Question ID
  resultsDF = abs( numStudents - df.groupby('QuestionID').agg({whichScores:'sum'}) ) / numStudents
  #print("\n\nDBG:  analyzing traditional questions\n\n", df)
  # Since Pandas idiotically removes the group column for no explicable reason, put it back
  resultsDF.index.name = 'QuestionID'
  resultsDF.reset_index(inplace=True)

  return resultsDF


def analyzeStudents(df, whichScores, contextDict):
  """
  Return a dataframe that has a row for each student taking a quiz, and
  a column for the ratio of questions that student missed.  # RPW:  Maybe we should flip this to "got right"?
  """
  numQuestions = len(set(df.QuestionID))

  # Compute the ratio of missed questions by aggregating over Question ID
  resultsDF = abs( numQuestions - df.groupby('StudentID').agg({whichScores:'sum'}) ) / numQuestions

  # Since Pandas idiotically removes the group column for no explicable reason, put it back
  resultsDF.index.name = 'StudentID'
  resultsDF.reset_index(inplace=True)

  return resultsDF
