from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import sessionmaker, scoped_session
#from sqlalchemy.ext.declarative import declarative_base

from flask import Flask, jsonify, abort

from flask_sqlalchemy import SQLAlchemy

import threading

APP = Flask(__name__)
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizlib.sqlite'
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
DB = SQLAlchemy(APP)

from models import Quiz, Distractor
# doing this after db is defined to avoid circular imports

class DataStore:
    
    def __init__(self):
        self.dbname='sqlite:///quizlib.sqlite'
        print('*** creating tables in SQLite3 DB')
        #__engine = create_engine(self.dbname, echo=False)
        #Base.metadata.create_all(__engine)
    
    
    def get_full_quiz(self, qid):
        q = self.get_quiz(qid)
        d = self.get_distractors_for_quiz(qid)
        quiz = {
            "question" : q.question,
            "answer" : q.answer,
            "options" : []
        }
        quiz['options'].append(q.answer)
        for zd in d:
            quiz['options'].append(zd.answer)
        return quiz

        
    def get_session(self):
        print('*** creating new session' + str(threading.get_ident()))
        engine = create_engine(self.dbname, echo=False)
        #Session = sessionmaker(bind=engine)
        #return Session()
        return scoped_session(sessionmaker(bind=engine))


    def get_quiz(self, qid):
        data = Quiz.query.filter_by(id=qid).first()
        return data


    def get_all_quizzes(self):
        data = Quiz.query.all()
        return data


    def get_all_distractors(self):
        data = Distractor.query.all()
        return data
    
    def get_distractors_for_quiz(self, qid):
        data = Distractor.query.filter_by(quiz_id=qid).all()
        return data

    def populate(self):
        '''Just populating the DB with some mock quizzes'''
        s = self.get_session()
        all_quizzes = [
                Quiz(   title=u'Sir Lancelot and the bridge keeper, part 1',
                        question=u'What... is your name?',
                        answer=u'Sir Lancelot of Camelot'),
                Quiz(   title=u'Sir Lancelot and the bridge keeper, part 2',
                        question=u'What... is your quest?', 
                        answer=u'To seek the holy grail'),
                Quiz(   title=u'Sir Lancelot and the bridge keeper, part 3',
                        question=u'What... is your favorite colour?', 
                        answer=u'Blue')
        ]
        
        s.add_all(all_quizzes)
        
        #TODO how to get the foreign keys
        qid=all_quizzes[0].id
        some_distractors = [
            Distractor(quiz_id=qid,answer=u'Sir Galahad of Camelot'),
            Distractor(quiz_id=qid,answer=u'Sir Arthur of Camelot'),
            Distractor(quiz_id=qid,answer=u'Sir Bevedere of Camelot'),
            Distractor(quiz_id=qid,answer=u'Sir Robin of Camelot'),
        ]
        
        qid=all_quizzes[0].id
        more_distractors = [
            Distractor(quiz_id=qid,answer=u'To bravely run away'),
            Distractor(quiz_id=qid,answer=u'To spank Zoot'),
            Distractor(quiz_id=qid,answer=u'To find a shrubbery')
        ]

        qid=all_quizzes[0].id
        yet_more_distractors = [
                Distractor(quiz_id=qid,answer=u'Green'),
                Distractor(quiz_id=qid,answer=u'Red'),
                Distractor(quiz_id=qid,answer=u'Yellow')
        ]

        s.add_all(some_distractors + more_distractors + yet_more_distractors)
                
        s.commit()
        s.close()



if __name__ == '__main__':
    ds = DataStore()
    ds.populate()