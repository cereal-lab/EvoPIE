import sys
import numpy as np
import pandas as pd

import dashboard.datalayer.generator as da
#import dashboard.datalayer.dbaccess as da
import dashboard.datalayer.utils as dataUtils



def analyzeStudents(df, whichScores, contextDict):
  """
  Return a dataframe that has a row for each student taking a quiz, and
  a column for the ratio of questions that student missed.  # RPW:  Maybe we should flip this to "got right"?
  """
  print("Got to analyze students")
  # Compute the average score of each student by aggregating over studentID ID
  resultsDF = df.groupby('StudentID').agg({'RevisedScore' : ['mean'], 'InitialScore' : ['mean']})

   # Since Pandas idiotically removes the group column for no explicable reason, put it back
  resultsDF.index.name = 'StudentID'
  resultsDF.reset_index(inplace=True)

  # Aggragating caused multilevel indexing to occur. This removes the 2nd level.
  resultsDF.columns = resultsDF.columns.droplevel(1)

  try:
    resultsDF = resultsDF.melt(id_vars=['StudentID'], value_vars=['RevisedScore','InitialScore'])
  except Exception as e:
      print("Distribution Didn't work:", e)


  return resultsDF


def unitTest():
  """
  Test to make sure this works.
  """
  df = da.GetScoresDataframe(0, 12,3)
  print("Number of students: ", len(set(df.StudentID)))
  print("Number of questions:", len(set(df.QuestionID)))

  contextDict = dict()
  print(analyzeStudents(df, 'InitialScore', contextDict)) 


if __name__ == '__main__':
  unitTest()