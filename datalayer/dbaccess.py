# pylint: disable=no-member
# pylint: disable=E1101

# This module is meant to provide a database access layer for the data
# analytics dashboard.

import numpy as np
import pandas as pd
import ast
import sys
import json

import datalayer.models as models
import analysislayer.utils as dataUtils

from flask_login import current_user


def IsValidDashboardUser():
  """
  Determine whether the user is properly logged in and is one of the roles that
  is permitted to see the dashboard data:  admin or instructor.  Return -1 for 
  not authenticated at all, 0 if authenticated but not a valid role, 1 if the role 
  instructor or admin.
  """
  validated = -1
  user = None

  # Try to get the current authenticated user and checking it's role
  try:
    if (current_user.is_authenticated):
      validated = 0
      user = models.User.query.filter(models.User.id == current_user.id).first()

      # If we didn't find a current user, refuse to validate the user
      if (user == None):    
        validated = -1

      # Otherwise, make sure the user is an instructor or an admin
      elif (user.is_instructor() or user.is_admin()):
        validated = 1

  # If we had any kind of problem, refuse to validate the user
  except:
    validated = -1

  return validated


def GetScoresDataframe(quizID, numQuestions=None, branching=None, maxNumStudents=None, quiet=True):
  """
  Given a quiz ID, retrieve all the student scores for the initial (pre-) and revised (post-)
  quizzes.  The result is a Pandas dataframe containing every student, question, and score.
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

  # Spin through every student attempt for all questions on the specified quiz
  for studentInstance in models.QuizAttempt.query.filter(models.QuizAttempt.quiz_id == quizID).all():
    try:
      # Convert the question results into python dictionaries
      initScores = studentInstance.initial_scores #ast.literal_eval(studentInstance.initial_scores)
      reviScores = studentInstance.revised_scores #ast.literal_eval(studentInstance.revised_scores)

      # Assume the same questions on the initial and revised quizzes, spin through these
      for questionStr in initScores:
        # Grab the field information for this question to make a new row
        StudentIDs    = pd.Series([int(studentInstance.student_id)], dtype='int')
        QuestionIDs   = pd.Series([int(questionStr)], dtype='int')
        InitialScores = pd.Series([initScores[questionStr]], dtype='float')
        RevisedScores = pd.Series([reviScores[questionStr]], dtype='float') 

        # Append a new row to the data frame
        dfNewRow = pd.DataFrame({'StudentID':StudentIDs, \
                                'QuestionID':QuestionIDs, \
                                'InitialScore':InitialScores, \
                                'RevisedScore':RevisedScores})    
        df = pd.concat([df, dfNewRow])  

    except:
      if not quiet:
        print("WARNING: QuizAttempt record", studentInstance.id, "was incomplete.  Ignoring this record.")

  return df


def GetQuestionDetailDataframe(quizID, questionID, whichScores, quiet=True):
  """
  Get all the details about the results on a particular question.  This will be used
  to build the bar plot for the question detail frame.
  """
  # Set a flag for whether the initial or revised scores were intended
  isInit =  whichScores.lower().find("init")
  textTruncationLength = 0

  responseID = -1
  question = models.Question.query.filter(models.Question.id == questionID).first()

  # First, let's build a dictionary for tallying things.  We start by having one entry that
  # represents the correct answer.  It's key will be "-1".
  #                                  QuestionID  QuestionText   ResponseID  ResponseText    CorrectResp  Count
  questionTallyDict = {responseID: (question.id, question.stem, responseID, question.answer, True, 0)}

  for studentInstance in models.QuizAttempt.query.filter(models.QuizAttempt.quiz_id == quizID).all():
    try:
      # Grab all the respones to the questions
      responses = None
      if isInit:
        responses = studentInstance.initial_responses
      else:
        responses = studentInstance.revised_responses

      # The responses fields are dictionaries where the key is the question ID (as a string)
      # and the value is "-1" is the student got it correct and the distractor ID (as a number)
      # if the student got it wrong.  So this gets that value out for the chosen question for this student & quiz.
      questionResponse = int(responses[str(questionID)])  ## RPW:  What if this quesiton wasn't taken by this student for this quiz?

      # If this response is in the tally dictionary, increment the count.  There are three cases:
      #   1) Student got this question right, then questionResponse will be "-1" and that entry already exists in the tally dictionary.
      #   2) Student got this wrong, but there's an entry in the dictionary already ...
      #   3) The first student to answer wrong with this distractor (go to the 'else' clause for that)
      if questionResponse in questionTallyDict:
        (QID, QText, ResponseID, ResponseText, CorrectResp, Count) = questionTallyDict[questionResponse]
        #QText = dataUtils.StripHTMLMarkers(QText, textTruncationLength)  # Strip HTML markup tags (etc, below)
        #ResponseText = dataUtils.StripHTMLMarkers(ResponseText, textTruncationLength)
        questionTallyDict[questionResponse] = (QID, QText, ResponseID, ResponseText, CorrectResp, Count+1)

      # Otherwise, create an entry with a count of 1.  The only way this else can happen is if this is
      # the first time a student has answered incorrectly with this particular distractor.
      else:
        distractor = models.Distractor.query.filter(models.Distractor.id == questionResponse).first()
        QText = dataUtils.StripHTMLMarkers(question.stem, textTruncationLength)
        ResponseText = dataUtils.StripHTMLMarkers(distractor.answer, textTruncationLength)
        questionTallyDict[questionResponse] = (question.id, QText, questionResponse, ResponseText, False, 1)
    except:
      if not quiet:
        print("WARNING: QuizAttempt record" + str(studentInstance.id) + "was incomplete.  Ignoring this record.")

  # Now build the Pandas dataframe
  QIDs, QText, RIDs, RText, Corrects, Counts = tuple(zip(*questionTallyDict.values()))
  df = pd.DataFrame({'QuestionID':pd.Series(QIDs, dtype='int'), \
                     'QuestionText':pd.Series(QText, dtype='string'), \
                     'ResponseID':pd.Series(RIDs, dtype='int'), \
                     'ResponseText':pd.Series(RText, dtype='string'), \
                     'CorrectResponse':pd.Series(Corrects, dtype='boolean'), \
                     'NumberStudents':pd.Series(Counts, dtype='int')})

  return df


def GetQuizOptionList():
  """
  Build a list of dictionaries containing the label string to display and the 
  ID to use for lookup based on on quizzes in the database.  Basically, this
  is a list of quizzes.
  """
  quizOptionList = []
  for quizInstance in models.Quiz.query.order_by(models.Quiz.id).all():
    optDict = {'label':quizInstance.title, 'value':int(quizInstance.id)}
    quizOptionList.append(optDict)
  return quizOptionList


def GetGlossaryTerms():
  terms   = pd.Series([], dtype='string')
  definitions = pd.Series([], dtype='string')

  df = pd.DataFrame({'Terms':terms, \
                     'Definitions':definitions})
  
  for termInstance in models.GlossaryTerm.query.order_by(models.GlossaryTerm.id).all():
    terms   = pd.Series([termInstance.term], dtype='string')
    definitions = pd.Series([termInstance.definition], dtype='string')

    dfNewRow = pd.DataFrame({'Terms':terms, \
                              'Definitions':definitions})
    
    df = pd.concat([df,dfNewRow])
      
  return df


def GetStoredWidgetObject(quiz_id, analysis_type, score_type, view_type):
  """
  Return the stored widget object that is uniquely identified by the quiz id, type of analysis,
  score type, and view type.  If that object isn't in the DB, return the default dcc object.
  """
  dccObject = None
  hashCheck = "NOHASH"
  dccContext = dict()

  try:
    key = models.WidgetStore.build_key(quiz_id, analysis_type, score_type, view_type)
    widget = models.WidgetStore.query.filter(models.WidgetStore.key == key).one()
    dccObject = widget.dccObject
    hashCheck = widget.hashCheck
    dccContext = json.loads(widget.dccContext)
  except:
    hashCheck = "NOHASH"
    dccObject = None
    dccContext = dict()

  return dccObject, hashCheck, dccContext


def PutStoredWidgetObject(quiz_id, analysis_type, score_type, view_type, hash_check, dcc_object, dcc_context):
  """
  Store the DCC widget object uniquely identified by the quiz id, type of analysis,
  score type, and view type into the data base
  """
  widget = None
  widgetKey = models.WidgetStore.build_key(quiz_id, analysis_type, score_type, view_type)

  # Try to find this widget in the table to update it
  try:
    widget = models.WidgetStore.query.filter(models.WidgetStore.key == widgetKey).one()
    widget.dccObject = dcc_object
    widget.dccContext = json.dumps(dcc_context)
    widget.hashCheck = hash_check
    models.DB.session.commit()
  except:
    widget = None

  # If it wasn't there, then add it!
  if widget == None:
    try:
      widget = models.WidgetStore(key=widgetKey,\
                                  quizID=quiz_id,\
                                  analysisType=analysis_type,\
                                  scoreType=score_type,\
                                  viewType=view_type,\
                                  hashCheck=hash_check,\
                                  dccObject=dcc_object,\
                                  dccContext=json.dumps(dcc_context))
      models.DB.session.add(widget)      
      models.DB.session.commit()
    except:
      print("ERROR:  Could not add widget ", widgetKey)
      raise
    