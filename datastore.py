from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
        


class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    def __repr__(self):
        return "Quiz(id='%d',title='%s',question='%s',solution = '%s')" % (self.id, self.title, self.question, self.answer)



class Distractor(Base):
    __tablename__ = 'distractors'
    id = Column(Integer, primary_key=True)
    quiz_id = Column(None, ForeignKey('quizzes.id'))
    answer = Column(String, nullable=False)
    def __repr__(self):
        return "Quiz(quiz_id=%d,id='%d',answer='%s')" % (self.quiz_id, self.id, self.answer)



class DataStore:
    
    def __init__(self):
        dbname='sqlite:///quizlib.sqlite'
        __engine = create_engine(dbname, echo=False)
        Base.metadata.create_all(__engine)
        

    def get_all_quizzes(self):
        __engine = create_engine(dbname, echo=False)
        __Session = sessionmaker(bind=__engine)
        s = __Session()
        data = s.query(Quiz)
        s.close()
        return data


    def get_all_distractors(self):
        __engine = create_engine(dbname, echo=False)
        __Session = sessionmaker(bind=__engine)
        s = __Session()
        data = s.query(Distractor)
        s.close()
        return data


    def populate(self):
        '''Just populating the DB with some mock quizzes'''
        self.__engine = create_engine(dbname, echo=False)
        self.__Session = sessionmaker(bind=self.__engine)
        s = self.__Session()
        s.add(Quiz(
                title=u'Sir Lancelot and the bridge keeper, part 1',
                question=u'What... is your name?',
                answer=u'Sir Lancelot of Camelot'))
        s.add(Quiz(
                title=u'Sir Lancelot and the bridge keeper, part 2',
                question=u'What... is your quest?', 
                answer=u'To seek the holy grail'))
        s.add(Quiz(
                title=u'Sir Lancelot and the bridge keeper, part 3',
                question=u'What... is your favorite colour?', 
                answer=u'Blue'))
        
        #TODO how to get the foreign keys
        s.add(Distractor(quiz_id=1,answer=u'Sir Galahad of Camelot'))
        s.add(Distractor(quiz_id=1,answer=u'Sir Arthur of Camelot'))
        s.add(Distractor(quiz_id=1,answer=u'Sir Bevedere of Camelot'))
        s.add(Distractor(quiz_id=1,answer=u'Sir Robin of Camelot'))

        s.add(Distractor(quiz_id=2,answer=u'To bravely run away'))
        s.add(Distractor(quiz_id=2,answer=u'To spank Zoot'))
        s.add(Distractor(quiz_id=2,answer=u'To find a shrubbery'))

        s.add(Distractor(quiz_id=3,answer=u'Green'))
        s.add(Distractor(quiz_id=3,answer=u'Red'))
        s.add(Distractor(quiz_id=3,answer=u'Yellow'))

        s.commit()
        s.close()



def main():
    ds = DataStore()
    ds.populate()



if __name__ == '__main__':
    main()
    