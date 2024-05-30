import flask
import re
import numpy as np


## General utility function shared by both application views
import datalayer.dbaccess as da

def GetSelectedQuizIDCookie(defaultVal):
  # Get the list of quizzes, and determine the default to use for the drop-down
  quizIDstr = defaultVal

  # If the quiz ID cookie is set, use that as the value for the drop down
  try:
    allcookies=dict(flask.request.cookies)
    if 'evopie_dashboard_quizid' in allcookies:
      quizIDstr = allcookies['evopie_dashboard_quizid']   
      print("DBG:::  Successfully got the 'evopie_dashboard_quizid' cookie=", quizIDstr)

  except:
    quizIDstr = defaultVal

  return quizIDstr


def SetSelectedQuizIDCookie(quizID, ctx):
  try:
    ctx.response.set_cookie('evopie_dashboard_quizid', str(quizID))
    print("DBG:::  Successfully set the 'evopie_dashboard_quizid' cookie to ", quizID)
  except:
    print("Could not set the 'evopie_dashboard_quizid' cookie")
  

def GetDataFromPrefix(propIDPrefix, inputItem, whichView, quiet=True):
  """
  Take the property ID prefix and parse it to determine which analysis we are selecting.
  """
  data = None

  # Indicate which axis points will fall along, when needed
  axisLabel = 'y'

  if not quiet:
    print('Input Item: ' + str(inputItem) + ",   View: " + str(whichView))

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


def StripContextInfo(ctx, whichView, quiet=True):
  """
  Convenience method to strip needed information from the context and return it. 
  This avoids repeating this code over and over
  """
  data = None
  whichScores = 'InitialScores'

  if ctx.triggered:
    # Context property ID will look something like this:  deca-question-InitialScore.tapNodeData
    inputItem = ctx.triggered[0]['value']
    propID = ctx.triggered[0]['prop_id']
    propIDPrefix = propID.split('-')[0]

    whichScores = propID.split('-')[2].split('.')[0]
    data = GetDataFromPrefix(propIDPrefix, inputItem, whichView, quiet)  

  return whichScores, data
