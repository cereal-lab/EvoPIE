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
    '''
    This class should encapsultate all the details of interacting with the database.
    This version is using Flqsk-SQLAlchemy ORM.
    If we revisit this decision, this should be the only part of the code to have
    to undergo modifications, without breaking its API.
    '''


    def __init__(self):
        self.dbname='sqlite:///quizlib.sqlite'
        DB.create_all()


    
    def get_question(self, qid):
        data = models.Question.query.filter_by(id=qid).first()
        return data



    def get_question_json(self, qid):
        '''
        Returns a dictionary with the question + answer + distractors.
        Answer and distractors are shuffled together as options from which
        the student will have to pick.
        '''
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



    def add_distractor_for_question(self, qid, dist):
        q = self.get_question(qid)
        if q != None:
            q.distractors.append(models.Distractor(answer=dist,question_id=qid))
            models.DB.session.commit()    



    def add_question(self, title, question, answer):
        q = models.Question(title=title, question=question, answer=answer)
        models.DB.session.add(q)
        models.DB.session.commit()



    def update_question(self, question_id, title, question, answer):
        q = self.get_question(question_id)
        if q != None:
            q.title = title
            q.question = question
            q.answer = answer
            models.DB.session.commit()
            return True
        else:
            return False
        
        
    
    def delete_question(self, question_id):
        q = self.get_question(question_id)
        if q != None:
            models.DB.session.delete(q)
            models.DB.session.commit()
            return True
        else:
            return False

    

    def get_distractors_for_question(self, qid):
        data = models.Distractor.query.filter_by(question_id=qid).all()
        #FIXME we could also fetch the question and just return its distractors field
        return data



    def get_distractors_for_question_json(self, qid):
        data = self.get_distractors_for_question(qid)
        result = []
        for d in data:
            result.append({ "answer": d.answer })
        return result
    



        # BEWARE
        # In the following methods, the distractor is identified by its index 
        # in the list of distractors for this question, instead of using its unique distractor ID.
        # We are here assuming that the queries from the DB will be idempotent
        # with respect to the ordering of the distractors.
        # The caller must also display them to the user in the same order.
        # It is not obvious this part of the API should be kept. In the long run, simply
        # use the routes that specify distractors by their IDs and let the caller
        # figure these out before to send us requests...



    def get_distractor_for_question(self, qid, index):
        #FIXME - see above
        all = self.get_distractors_for_question(qid)
        if len(all) > index:
            return all[index]
        else:
            return None
        



    def get_distractor_for_question_json(self,qid, index):
        #FIXME - see above
        d = self.get_distractor_for_question(qid, index)
        if d == None:
            return None
        else:
            return { "answer": d.answer }
            
        
    
    def update_distractor_for_question(self, qid, index, answer):
        #FIXME - see above
        d = self.get_distractor_for_question(qid, index)
        if d == None:
            return False
        else:
            d.answer = answer
            models.DB.session.commit()
            return True
    


    def delete_distractor_for_question(self, qid, index):
        #FIXME - see above
        d = self.get_distractor_for_question(qid, index)
        if d == None:
            return False
        else:
            models.DB.session.delete(d)
            models.DB.session.commit()
            return True
    


    # The following methods use a proper distractor_id



    def get_distractor(self, did):
        d = models.Distractor.query.filter_by(id=did).first()
        return d
        


    def get_distractor_json(self, qid, did):
        d = self.get_distractor(did)
        if d == None:
            return None
        else:
            return { "answer": d.answer }
            
        
    
    def update_distractor(self, did, answer):
        d = self.get_distractor(did)
        if d == None:
            return False
        else:
            d.answer = answer
            models.DB.session.commit()
            return True
    


    def delete_distractor(self, did):
        d = self.get_distractor(did)
        if d == None:
            return False
        else:
            models.DB.session.delete(d)
            models.DB.session.commit()
            return True
    
        
        
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

