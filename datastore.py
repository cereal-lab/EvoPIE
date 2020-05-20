# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime.
# This is a way to tell pylint to let it be
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import sessionmaker, scoped_session

from flask import Flask, jsonify, abort

from flask_sqlalchemy import SQLAlchemy

from random import shuffle # to shuffle lists

APP = Flask(__name__)
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizlib.sqlite'
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
DB = SQLAlchemy(APP)

import models
# doing this after db is defined to avoid circular imports



class DataStore:


    def __init__(self):
        self.dbname='sqlite:///quizlib.sqlite'
        DB.create_all()

    
    def get_question(self, qid):
        data = models.Question.query.filter_by(id=qid).first()
        return data


    def get_question_json(self, qid):
        q = self.get_question(qid)
        if q == None:
            return None
        quiz = {
            "title" : q.title,
            "question" : q.question,
            "answer" : q.answer,
            "options" : []
        }
        quiz['options'].append(q.answer)
        for d in q.distractors:
            quiz['options'].append(d.answer)
        shuffle(quiz['options'])
        return quiz


    def get_all_questions(self):
        data = models.Question.query.all()
        return data
    
    
    def get_all_questions_json(self):
        result=[]
        quizzes = models.Question.query.all()
        for q in quizzes:
            result.append(self.get_question_json(q.id))
        return result


    def get_all_distractors(self):
        data = models.Distractor.query.all()
        return data
    

    def get_distractors_for_question(self, qid):
        data = models.Distractor.query.filter_by(question_id=qid).all()
        return data


    def add_distractor_for_question(self, qid, dist):
        q = self.get_question(qid)
        if q != None:
            q.distractors.append(models.Distractor(answer=dist,question_id=qid))
            models.DB.session.commit()    


    def populate(self):
        '''
            Just populating the DB with some mock quizzes
        '''
        # For some reason Flask restarts the app when we launch it with
        # pipenv run python inn.py
        # as a result, we populate twice and get too many quizzes / distractors
        # let's fix this by deleting all data from the tables first
        models.Question.query.delete()
        models.Distractor.query.delete()
        models.DB.session.commit() # don't forget to commit or the DB will be locked

        s = models.DB.session
        
        all_mcqs = [
                models.Question(    title=u'Sir Lancelot and the bridge keeper, part 1',
                                question=u'What... is your name?',
                                answer=u'Sir Lancelot of Camelot'),
                models.Question(    title=u'Sir Lancelot and the bridge keeper, part 2',
                                question=u'What... is your quest?', 
                                answer=u'To seek the holy grail'),
                models.Question(    title=u'Sir Lancelot and the bridge keeper, part 3',
                                question=u'What... is your favorite colour?', 
                                answer=u'Blue')
        ]
        
        s.add_all(all_mcqs)
        s.commit()        
        # need to commit right now
        # If not, the qid below will not be added in the distractors table's rows

        qid=all_mcqs[0].id
        some_distractors = [
            models.Distractor(question_id=qid,answer=u'Sir Galahad of Camelot'),
            models.Distractor(question_id=qid,answer=u'Sir Arthur of Camelot'),
            models.Distractor(question_id=qid,answer=u'Sir Bevedere of Camelot'),
            models.Distractor(question_id=qid,answer=u'Sir Robin of Camelot'),
        ]
        
        qid=all_mcqs[1].id
        more_distractors = [
            models.Distractor(question_id=qid,answer=u'To bravely run away'),
            models.Distractor(question_id=qid,answer=u'To spank Zoot'),
            models.Distractor(question_id=qid,answer=u'To find a shrubbery')
        ]

        qid=all_mcqs[2].id
        yet_more_distractors = [
            models.Distractor(question_id=qid,answer=u'Green'),
            models.Distractor(question_id=qid,answer=u'Red'),
            models.Distractor(question_id=qid,answer=u'Yellow')
        ]

        s.add_all(some_distractors + more_distractors + yet_more_distractors)
        s.commit()

