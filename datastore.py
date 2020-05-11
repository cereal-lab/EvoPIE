from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import threading

Base = declarative_base()
        


class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    def __repr__(self):
        return "Quiz(id='%d',title='%s',question='%s',solution='%s')" % (self.id, self.title, self.question, self.answer)



class Distractor(Base):
    __tablename__ = 'distractors'
    id = Column(Integer, primary_key=True)
    quiz_id = Column(None, ForeignKey('quizzes.id'))
    answer = Column(String, nullable=False)
    def __repr__(self):
        return "Quiz(quiz_id=%d,id='%d',answer='%s')" % (self.quiz_id, self.id, self.answer)



class DataStore:
    
    def __init__(self):
        self.dbname='sqlite:///quizlib.sqlite'
        print('*** creating tables in SQLite3 DB')
        #__engine = create_engine(self.dbname, echo=False)
        #Base.metadata.create_all(__engine)
        
    def get_session(self):
        print('*** creating new session' + str(threading.get_ident()))
        engine = create_engine(self.dbname, echo=False)
        Session = sessionmaker(bind=engine)
        return Session()

    def get_all_quizzes(self):
        s = self.get_session()
        data = s.query(Quiz)
        s.close()
        return data


    def get_all_distractors(self):
        s = self.get_session()
        data = s.query(Distractor)
        s.close()
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