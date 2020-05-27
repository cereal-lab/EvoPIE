# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from sqlalchemy import Table, Column, Integer, String, ForeignKey
from random import shuffle # to shuffle lists

from evopie import models # get also DB from there



class DataStore:
    '''
    This class should encapsultate all the details of interacting with the database.
    This version is using Flask-SQLAlchemy ORM.
    If we revisit this decision, this should be the only part of the code to have
    to undergo modifications, without breaking its API.
    '''


    def __init__(self):
        #models.DB.create_all()
        #FIXME we should not recreate the DB at each run; use flask CLI commands
        pass


    
    def get_question(self, qid):
        return models.Question.query.get(qid)



    def get_question_json(self, qid):
        '''
        Returns a dictionary with the question + answer + ALL distractors.
        The fact that all distractors are included is the main difference
        between Question and QuizQuestion.
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

        quiz['options'] = [d.answer for d in q.distractors]
        quiz['options'].append(q.answer)
        shuffle(quiz['options'])

        return quiz



    def get_all_questions(self):
        return models.Question.query.all()

    
    

    def get_all_questions_json(self):
        result=[]
        quizzes = models.Question.query.all()
        for q in quizzes:
            result.append(self.get_question_json(q.id))
        return result



    def get_all_distractors(self):
        return models.Distractor.query.all()



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
        
        
    
    def get_distractors_for_question(self, qid):
        return models.Question.query.get(qid).distractors



    def get_distractors_for_question_json(self, qid):
        data = self.get_distractors_for_question(qid)
        result = []
        for d in data:
            result.append({ "answer": d.answer })
        return result
    



        #NOTE using index for distractors instead of IDs.
        # In the following methods, the distractor is identified by its index 
        # in the list of distractors for this question, instead of using its unique distractor ID.
        # We are here assuming that the queries from the DB will be idempotent
        # with respect to the ordering of the distractors.
        # The caller must also display them to the user in the same order.
        # It is not obvious this part of the API should be kept. In the long run, simply
        # use the routes that specify distractors by their IDs and let the caller
        # figure these out before to send us requests...



    def get_distractor_for_question(self, qid, index):
        #NOTE - see above
        all = self.get_distractors_for_question(qid)
        if len(all) > index:
            return all[index]
        else:
            return None
        



    def get_distractor_for_question_json(self, qid, index):
        #NOTE - see above
        d = self.get_distractor_for_question(qid, index)
        if d == None:
            return None
        else:
            return { "answer": d.answer }
            
        
    
    def update_distractor_for_question(self, qid, index, answer):
        #NOTE - see above
        d = self.get_distractor_for_question(qid, index)
        if d == None:
            return False
        else:
            d.answer = answer
            models.DB.session.commit()
            return True
    


    # The following methods use a proper distractor_id



    def get_distractor(self, did):
        return models.Distractor.query.get(did)
        


    def get_distractor_json(self, did):
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
    


    def add_quiz_question(self, question_id, distractors_ids):
        q = self.get_question(question_id)
        if q == None: 
            return False

        distractors = []
        for id in distractors_ids:
            obj = self.get_distractor(id)
            if obj == None:
                return False
            else:
                distractors.append(obj)

        qq = models.QuizQuestion(question=q)
        for d in distractors:
            qq.distractors.append(d)
        models.DB.session.add(qq)
        models.DB.session.commit()
        return True
        
        
        
    def get_all_quiz_questions(self):
        return models.QuizQuestion.query.all()


    def get_all_quiz_questions_json(self):
        result=[]
        qq = self.get_all_quiz_questions()
        for q in qq:
            result.append(self.get_quiz_question_json(q.id))
        return result
    
    
    
    def get_quiz_question(self, qqid):
        return models.QuizQuestion.query.filter_by(id=qqid).first()
    
    
    
    def get_quiz_question_json(self, qqid):
        qq = self.get_quiz_question(qqid)
        if qq == None:
            return None
        
        result = {  "title": qq.question.title,
                    "question": qq.question.question,
                    "answer": qq.question.answer,
                    "options": [] }
        
        result['options'].append(qq.question.answer)
        for d in qq.distractors:
            result['options'].append(d.answer)
        shuffle(result['options'])
        return result

    
    
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

        all_mcqs = [
                models.Question(title=u'Sir Lancelot and the bridge keeper, part 1',
                                question=u'What... is your name?',
                                answer=u'Sir Lancelot of Camelot'),
                models.Question(title=u'Sir Lancelot and the bridge keeper, part 2',
                                question=u'What... is your quest?', 
                                answer=u'To seek the holy grail'),
                models.Question(title=u'Sir Lancelot and the bridge keeper, part 3',
                                question=u'What... is your favorite colour?', 
                                answer=u'Blue')
        ]
        
        models.DB.session.add_all(all_mcqs)
        models.DB.session.commit()        
        # need to commit right now; if not, the qid below will not be added in the distractors table's rows

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

        models.DB.session.add_all(some_distractors + more_distractors + yet_more_distractors)
        models.DB.session.commit()


