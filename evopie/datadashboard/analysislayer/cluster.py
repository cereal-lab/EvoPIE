import sys
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.manifold import MDS
from sklearn.metrics import davies_bouldin_score

import datalayer.dbaccess as da
import evopie.datadashboard.utils as dataUtils


## RPW:  Quiz 1, question view should be able to cluster, why can't it?  Fix

def analyzeQuestions(df, whichScores, contextDict):
  """
  Perform an MDS/klustering analysis of the question space.  That is, each point to be
  clustered represents a specific question.  Questions are treated as vectors of student
  responses, and that n-dimension space is reduced to 2 dim using MDS, then the embedded
  space is clustered.  Thus, each point in the embedded space represents a 2-dim reduction
  of a specific question in terms of how all students scored on that question.
  """
  maxClusters = contextDict["maxClusters"]
  embeddedSpace = None

  initialMatrix, revisedMatrix, studentIDs, questionIDs = dataUtils.convertDataFrameToMatrices(df, whichScores)

  initRows, initCols = initialMatrix.shape
  reviRows, reviCols = revisedMatrix.shape

  # Don't both clustering if the initial matrix doesn't have enough data
  if (initRows < 2) or (initCols < 2):
    print("WARNING:  The initial question matrix has insufficient information to cluster")
    maxClusters = 1 # Just to skip the loop below

  # Don't both clustering if the revised matrix doesn't have enough data
  elif (reviRows < 2) or (reviCols < 2):
    print("WARNING:  The initial question matrix has insufficient information to cluster")
    maxClusters = 1 # Just to skip the loop below

  # Transform the appropriate matrix into a 2D space using an MDS based model
  # That's the space in which we will cluster
  else:
    # Get the model builder for multi-dimensional scaling, initilize embedded space
    embeddingModel = MDS(n_components=2, normalized_stress="auto")
    if (whichScores == 'RevsedMatrix'):
        embeddedSpace = embeddingModel.fit_transform(initialMatrix.transpose())
    else:
        embeddedSpace = embeddingModel.fit_transform(revisedMatrix.transpose())

  # Learn the k-means clusters model over this 2D data, get the cluster labels   
  kmModel = None
  kmLabels = None
  kmQuality = sys.float_info.max  # Because DB is a minimization, start at the max val

  # Try to find the best k that cluseters the best, minimizing DB score
  numClusters = 1
  while numClusters <= maxClusters:
    try:
      numClusters += 1
      model = KMeans(n_clusters=numClusters, n_init="auto")
      model.fit(embeddedSpace)
      labels = model.labels_.tolist()
      quality = davies_bouldin_score(embeddedSpace, labels)
      if (quality < kmQuality):
        kmModel = model
        kmLabels = labels
        kmQuality = quality
    except:
      print("WARNING:  Cannot cluster questions with k >=", numClusters)
      numClusters = sys.maxsize  # Skip the rest of the loop

  # Create the return data frame columns
  X          = pd.Series([], dtype='float')
  Y          = pd.Series([], dtype='float')
  GrpCounter = pd.Series([], dtype='float')
  Cluster    = pd.Series([], dtype='int')
  QuestionID = pd.Series([], dtype='category')

  returnDF = pd.DataFrame({'X':X, \
                           'Y':Y, \
                           'GrpCounter':GrpCounter, \
                           'Cluster':Cluster, \
                           'QuestionID':QuestionID})      

  # Grow these columns from the dimensionally reduced dataset
  if not kmModel == None:
    groupCounts = [0] * max(kmLabels)
    for ptIdx in range(embeddedSpace.shape[0]):
        X = pd.Series([embeddedSpace[ptIdx,0]], dtype='float')
        Y = pd.Series([embeddedSpace[ptIdx,1]], dtype='float')
        clusterid = kmLabels[ptIdx]
        GrpCounter = pd.Series([groupCounts[clusterid-1]], dtype='float')
        groupCounts[clusterid-1] += 1
        Cluster = pd.Series([clusterid], dtype='int')          
        QuestionID = pd.Series([questionIDs[ptIdx]], dtype='category')                   

        # Assemble a new row then add it to the data frame
        dfNewRow = pd.DataFrame({'X':X, \
                                 'Y':Y, \
                                 'GrpCounter':GrpCounter, \
                                 'Cluster':Cluster, \
                                 'QuestionID':QuestionID})    

        returnDF = pd.concat([returnDF, dfNewRow])  

  else:
    print("WARNING:  No clustering is possible. [ question analysis, ", whichScores, "]")         
    # The data frame will be empty if none of the clusters were possible
   
  return returnDF



def analyzeStudents(df, whichScores, contextDict):
  """
  Perform an MDS/klustering analysis of the student space.  That is, each point to be
  clustered represents a specific student.  Students are treated as vectors of question
  responses, and that n-dimension space is reduced to 2 dim using MDS, then the embedded
  space is clustered.  Thus, each point in the embedded space represents a 2-dim reduction
  of a specific student's respones.
  """
  maxClusters = contextDict["maxClusters"]
  embeddedSpace = None

  initialMatrix, revisedMatrix, studentIDs, questionIDs = dataUtils.convertDataFrameToMatrices(df)

  initRows, initCols = initialMatrix.shape
  reviRows, reviCols = revisedMatrix.shape

  # Don't bother clustering if the initial matrix doesn't have enough data
  if (initRows < 2) or (initCols < 2):
    print("WARNING:  The initial student matrix has insufficient information to cluster")
    maxClusters = 1 # Just to skip the loop below

  # Don't bother clustering if the revised matrix doesn't have enough data
  elif (reviRows < 2) or (reviCols < 2):
    print("WARNING:  The initial student matrix has insufficient information to cluster")
    maxClusters = 1 # Just to skip the loop below

  # Transform the appropriate matrix into a 2D space using an MDS based model
  # That's the space in which we will cluster
  else:
    # Get the model builder for multi-dimensional scaling
    embeddingModel = MDS(n_components=2, normalized_stress="auto")

    if (whichScores == 'RevsedMatrix'):
        embeddedSpace = embeddingModel.fit_transform(initialMatrix) # Do not transpose here
    else:
        embeddedSpace = embeddingModel.fit_transform(revisedMatrix) # Do not transpose here

  # These will be the result variables for k-means clusters models over this 2D data
  kmModel = None
  kmLabels = None 
  kmQuality = sys.float_info.max  # Because DB is a minimization, start at the max val

  # Try to find the best clustering for 2 .. maxClusters
  numClusters = 1
  while numClusters <= maxClusters:
    try:
      numClusters += 1
      model = KMeans(n_clusters=numClusters, n_init="auto")
      model.fit(embeddedSpace)
      labels = model.labels_.tolist()
      quality = davies_bouldin_score(embeddedSpace, labels)
      #print(quality)
      if (quality < kmQuality):
        kmModel = model
        kmLabels = labels
        kmQuality = quality
    except:
      print("WARNING:  Cannot cluster students with k >=", numClusters)
      numClusters = sys.maxsize  # Skip the rest of the loop

  # Create the return data frame columns
  X          = pd.Series([], dtype='float')
  Y          = pd.Series([], dtype='float')
  GrpCounter = pd.Series([], dtype='float')
  Cluster    = pd.Series([], dtype='int')
  StudentID  = pd.Series([], dtype='category')

  returnDF = pd.DataFrame({'X':X, \
                           'Y':Y, \
                           'GrpCounter':GrpCounter, \
                           'Cluster':Cluster, \
                           'StudentID':StudentID})      

  # Grow these columns from the dimensionally reduced dataset
  if not kmModel == None:
    groupCounts = [0] * max(kmLabels)
    for ptIdx in range(embeddedSpace.shape[0]):
        X          = pd.Series([embeddedSpace[ptIdx,0]], dtype='float')
        Y          = pd.Series([embeddedSpace[ptIdx,1]], dtype='float')
        clusterid = kmLabels[ptIdx]
        GrpCounter = pd.Series([groupCounts[clusterid-1]], dtype='float')
        groupCounts[clusterid-1] += 1
        #print(clusterid)
        Cluster    = pd.Series([clusterid], dtype='int')         
        StudentID  = pd.Series([studentIDs[ptIdx]], dtype='category')   

        # Assemble these into a new row, then add it to the dataframe
        dfNewRow = pd.DataFrame({'X':X, \
                                 'Y':Y, \
                                 'GrpCounter':GrpCounter, \
                                 'Cluster':Cluster, \
                                 'StudentID':StudentID})            

        returnDF = pd.concat([returnDF, dfNewRow]) 

  else:
    print("WARNING:  No clustering is possible. [ student analysis, ", whichScores, "]")         
    # The data frame will be empty if none of the clusters were possible

  return returnDF



def unitTest():
  """
  Test to make sure this works.
  """
  df = da.GetScoresDataframe(1, 12, 3)
  print("Number of students: ", len(set(df.StudentID)))
  print("Number of questions:", len(set(df.QuestionID)))

  contextDict = {}
  print(analyzeQuestions(df, 'InitialScore', contextDict)) 


if __name__ == '__main__':
  unitTest()