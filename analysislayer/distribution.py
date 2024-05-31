import sys
import numpy as np
import pandas as pd

import analysislayer.utils as dataUtils
from datalayer import LOGGER


def analyzeStudents(df, whichScores, contextDict):
  """
  Return a dataframe that has a row for each student taking a quiz, and
  a column for the ratio of questions that student missed.  # RPW:  Maybe we should flip this to "got right"?
  """
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
      LOGGER.error("Distribution Didn't work:" + str(e))


  return resultsDF

