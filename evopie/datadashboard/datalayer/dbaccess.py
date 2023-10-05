# pylint: disable=no-member
# pylint: disable=E1101

# This module is meant to provide a database access layer for the data
# analytics dashboard.

import numpy as np
import pandas as pd
import ast
import sys

#import evopie.datadashboard.datalayer.models as models
import evopie.models as models
import evopie.datadashboard.datalayer.utils as dataUtils

## RPW:  This is going to be problematic ...
#from dashapp import dashapp_context
from evopie import dashapp_context

def GetScoresDataframe(quizID, numQuestions=None, branching=None, maxNumStudents=None, quiet=False):
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
  with dashapp_context:
    for studentInstance in models.QuizAttempt.query.filter(models.QuizAttempt.quiz_id == quizID):
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
          #print("DBG:      question=", questionStr, ",  init=", initScores[questionStr])

          # Append a new row to the data frame
          dfNewRow = pd.DataFrame({'StudentID':StudentIDs, \
                                  'QuestionID':QuestionIDs, \
                                  'InitialScore':InitialScores, \
                                  'RevisedScore':RevisedScores})    
          df = pd.concat([df, dfNewRow])  

      except:
        if not quiet:
          print("WARNING: QuizAttempt record", studentInstance.id, "was incomplete.  Ignoring this record.")
          #print("DBG:  student=", studentInstance.student_id, ",  initScores=", studentInstance.initial_scores, "  type(initScores)=", type(studentInstance.initial_scores))
          #sys.exit(1)

  return df


def GetQuestionDetailDataframe(quizID, questionID, whichScores, quiet=False):
  """
  Get all the details abo
  """
  # Set a flag for whether the initial or revised scores were intended
  isInit =  whichScores.lower().find("init")
  textTruncationLength = 0

  with dashapp_context:
    responseID = -1
    question = models.Question.query.filter(models.Question.id == questionID).first()

    # First, let's build a dictionary for tallying things.
    #                                  QuestionID  QuestionText   ResponseID  ResponseText    CorrectResp  Count
    questionTallyDict = {responseID: (question.id, question.stem, responseID, question.answer, True, 0)}
    #print("DBG::::: ", questionID, question.id, responseID, question.answer[0:30])

    for studentInstance in models.QuizAttempt.query.filter(models.QuizAttempt.quiz_id == quizID):
      try:
        # Grab all the respones to the questions
        responses = None
        if isInit:
          responses = ast.literal_eval(studentInstance.initial_responses)
        else:
          responses = ast.literal_eval(studentInstance.revised_responses)          

        questionResponse = int(responses[str(questionID)])

        # If this response is in the tally dictionary, increment the count
        if questionResponse in questionTallyDict:
          (QID, QText, ResponseID, ResponseText, CorrectResp, Count) = questionTallyDict[questionResponse]
          QText = dataUtils.StripHTMLMarkers(QText, textTruncationLength)  # Strip HTML markup tags (etc, below)
          ResponseText = dataUtils.StripHTMLMarkers(ResponseText, textTruncationLength)
          questionTallyDict[questionResponse] = (QID, QText, ResponseID, ResponseText, CorrectResp, Count+1)

        # Otherwise, create an entry with a count of 1
        else:
          distractor = models.Distractor.query.filter(models.Distractor.id == questionResponse).first()
          QText = dataUtils.StripHTMLMarkers(question.stem, textTruncationLength)
          ResponseText = dataUtils.StripHTMLMarkers(distractor.answer, textTruncationLength)
          questionTallyDict[questionResponse] = (question.id, QText, questionResponse, \
                                                ResponseText, False, 1)
      except:
        if not quiet:
          print("WARNING: QuizAttempt record", studentInstance.id, "was incomplete.  Ignoring this record.")

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
  Build a list of dictionaries containing the lable string to display and the 
  ID to use for lookup based on on quizzes in the database.  Basically, this
  is a list of quizzes.
  """
  quizOptionList = []
  with dashapp_context:
    for quizInstance in models.Quiz.query.order_by(models.Quiz.id).all():
      optDict = {'label':quizInstance.title, 'value':int(quizInstance.id)}
      quizOptionList.append(optDict)
  return quizOptionList


def GetGlossaryTerms():
  terms   = pd.Series([], dtype='string')
  definitions = pd.Series([], dtype='string')

  df = pd.DataFrame({'Terms':terms, \
                     'Definitions':definitions})
  
  with dashapp_context:
    for termInstance in models.GlossaryTerm.query.order_by(models.GlossaryTerm.id).all():
      terms   = pd.Series([termInstance.term], dtype='string')
      definitions = pd.Series([termInstance.definition], dtype='string')

      dfNewRow = pd.DataFrame({'Terms':terms, \
                               'Definitions':definitions})
      
      df = pd.concat([df,dfNewRow])
      
  return df