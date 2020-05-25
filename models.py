# pylint: disable=no-member
# pylint: disable=E1101 

from flaskcore import DB


class Question(DB.Model):
    '''
    A Question object contains both the text of the question to be 
    posed to students, along with its solution.
    The solution will always appear as a response option in the
    Multiple Choice Question presentation.
    '''

    id = DB.Column(DB.Integer, primary_key=True)

    title = DB.Column(DB.String, nullable=False)
    question = DB.Column(DB.String, nullable=False)
    answer = DB.Column(DB.String, nullable=False)
    
    # 1-to-many with Distractor
    distractors = DB.relationship('Distractor', backref='question', lazy=True)
    
    # 1-to-many with QuizQuestion
    quiz_questions = DB.relationship('QuizQuestion', backref='question', lazy=True)
    
    def __repr__(self):
        return "Question(id='%d',title='%s',question='%s',solution='%s')" % (self.id, self.title, self.question, self.answer)



# association table for many-to-many association between QuizQuestion and Distractor
quiz_questions_hub = DB.Table('quiz_questions_hub',
    DB.Column('quiz_question_id',   DB.Integer, DB.ForeignKey('quiz_question.id'),  primary_key=True),
    DB.Column('distractor_id',      DB.Integer, DB.ForeignKey('distractor.id'),     primary_key=True)  
)



class Distractor(DB.Model):
    '''
    A Distractor object is a plausible but wrong answer to a Question.
    '''
    
    id = DB.Column(DB.Integer, primary_key=True)

    answer = DB.Column(DB.String, nullable=False)
    
    # to allow for 1-to-many relationship Question / Distractor
    question_id = DB.Column(None, DB.ForeignKey('question.id'))
    
    def __repr__(self):
        return "Distractor(id='%d',question_id=%d,answer='%s')" % (self.question_id, self.id, self.answer)





class QuizQuestion(DB.Model):
    '''
    A QuizQuestion object is built based on a Question and its related Distractors.
    It is the object that will be rendered to students.
    '''
    # NOTE auto-generated table is named quiz_question as conversion to lowercase of the above camel case
    
    id = DB.Column(DB.Integer, primary_key=True)

    # to allow for 1-to-many relationship Question / QuizQuestion
    question_id = DB.Column(None, DB.ForeignKey('question.id'), nullable=False)

    
    # many-to-many with Distractor
    distractors = DB.relationship('Distractor', secondary=quiz_questions_hub, lazy='subquery',
        backref=DB.backref('quiz_questions', lazy=True))
    # these are the distractors that have been selected, among all available distractors
    # for a given question, to be features in this particular question to appear in a quiz



#Table used to implement the many-to-many relationship between QuizQuestions and Quizzes
quizzes_hub = DB.Table('quizzes_hub',
   DB.Column('quiz_id',             DB.Integer, DB.ForeignKey('quiz.id'),           primary_key=True),
   DB.Column('quiz_question_id',    DB.Integer, DB.ForeignKey('quiz_question.id'),  primary_key=True)
)



class Quiz(DB.Model):
   '''
   A Quiz object is a collection of QuizQuestion objects to be presented as a complete quiz
   to students.
   '''

   id = DB.Column(DB.Integer, primary_key=True)

   quiz_questions = DB.relationship('QuizQuestion', secondary=quizzes_hub, lazy='subquery',
       backref=DB.backref('quizzes', lazy=True))
