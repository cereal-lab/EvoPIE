# pylint: disable=no-member
# pylint: disable=E1101 
from datastore import DB
#watch out for circular imports



class Question(DB.Model):
    '''
    A Question object contains both the text of the question to be 
    posed to students, along with its solution.
    The solution will always appear as a response option in the
    Multiple Choice Question presentation.
    '''
    __tablename__ = 'questions'
    id = DB.Column(DB.Integer, primary_key=True)
    title = DB.Column(DB.String, nullable=False)
    question = DB.Column(DB.String, nullable=False)
    answer = DB.Column(DB.String, nullable=False)
    distractors = DB.relationship('Distractor', backref='quiz', lazy=True)

    def __repr__(self):
        return "Question(id='%d',title='%s',question='%s',solution='%s')" % (self.id, self.title, self.question, self.answer)



class Distractor(DB.Model):
    '''
    A Distractor object is a plausible but wrong answer to a Question.
    '''
    __tablename__ = 'distractors'
    id = DB.Column(DB.Integer, primary_key=True)
    question_id = DB.Column(None, DB.ForeignKey('questions.id'))
    answer = DB.Column(DB.String, nullable=False)
    def __repr__(self):
        return "Distractor(id='%d',question_id=%d,answer='%s')" % (self.question_id, self.id, self.answer)



class MCQ(DB.Model):
    '''
    A MCQ object is built based on a Question and its related Distractors.
    It is the object that will be rendered to students.
    '''
    __tablename__ = 'MCQs'
    id = DB.Column(DB.Integer, primary_key=True)
    question_id = DB.Column(None, DB.ForeignKey('questions.id'))
    question = DB.relationship('Question', backref='mcqs', lazy=True)
    


# Table used to implement the many-to-many relationship between 
# MCQs and Quizzes
quizhub = DB.Table(
    'quizhub',
    DB.Column('quiz_id', DB.Integer, DB.ForeignKey('quizzes.id'), primary_key=True),
    DB.Column('mcq_id', DB.Integer, DB.ForeignKey('MCQs.id'), primary_key=True)
)



class Quiz(DB.Model):
    '''
    A Quiz object is a collection of MCQs to be presented as a complete quiz
    to students.
    '''
    __tablename__ = 'quizzes'
    id = DB.Column(DB.Integer, primary_key=True)
    mcqs = DB.relationship('MCQ', secondary=quizhub, lazy='subquery',
        backref=DB.backref('quizzes', lazy=True))
