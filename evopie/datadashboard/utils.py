## General utility function shared by both application views
#import evopie.datadashboard.datalayer.generator as da
import evopie.datadashboard.datalayer.dbaccess as da


class ApplicationStateSingletonClass:
  """
  Singleton class to manage the state of the application with respect to which quiz is currently selected
  """
  QuizOptions = None
  QuizID = None
  QuizDF = None
  QuizDropDown = None
  
  def __init__(self):
    if ApplicationStateSingletonClass.QuizOptions == None:
      ApplicationStateSingletonClass.QuizOptions = da.GetQuizOptionList() 
      ApplicationStateSingletonClass.QuizID = ApplicationStateSingletonClass.QuizOptions[0]['value']
      ApplicationStateSingletonClass.QuizDF = da.GetScoresDataframe(ApplicationStateSingletonClass.QuizID, 17, 3, 22)
      print("DBG:  The application state singleton just got reinitialized!!!!!!!!!!!!!!!!!")

  def SetQuizID(self, inQuizID):
    ApplicationStateSingletonClass.QuizID = inQuizID
    print("DBG:  -----> The application state is setting the quiz ID to", inQuizID)

  def SetQuizDF(self, inQuizDF):
    ApplicationStateSingletonClass.QuizDF = inQuizDF


# Declare a global variable of the singleton class to use by questionview and studentview
gApplicationState = ApplicationStateSingletonClass()


  
def GetDataFromPrefix(propIDPrefix, inputItem, whichView, quiet=False):
  """
  Take the property ID prefix and parse it to determine which analysis we are selecting.
  """
  data = None

  # Indicate which axis points will fall along, when needed
  axisLabel = 'y'

  if not quiet:
    print('Input Item:', inputItem, ",   View:", whichView)

  if inputItem is not None:
    if propIDPrefix == 'deca':
      data   = inputItem['id']
    elif propIDPrefix == 'heatmap':
      data = inputItem['points'][0][axisLabel]      
    elif propIDPrefix == 'mds':
      data = inputItem['points'][0]['text'].split(' ')[1]
    elif propIDPrefix == 'ids':
      data = inputItem['points'][0]['label'].split(' ')[1]
    elif propIDPrefix == 'trad':
      data = inputItem['points'][0]['label'].split(' ')[1]

  return data


def StripContextInfo(ctx, whichView, quiet=False):
  """
  Convenience method to strip needed information from the context and return it. 
  This avoids repeating this code over and over
  """
  data = None
  whichScores = 'InitialScores'

  #if not quiet:
  #  print("CTX: ", ctx.triggered, "\n ::: ", ctx.states)
  
  if ctx.triggered:
    # Context property ID will look something like this:  deca-question-InitialScore.tapNodeData
    inputItem = ctx.triggered[0]['value']
    propID = ctx.triggered[0]['prop_id']
    propIDPrefix = propID.split('-')[0]

    whichScores = propID.split('-')[2].split('.')[0]
    data = GetDataFromPrefix(propIDPrefix, inputItem, whichView, quiet)  

  return whichScores, data
