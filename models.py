from datastore import DB
#watch out for circular imports


class Quiz(DB.Model):
    __tablename__ = 'quizzes'
    id = DB.Column(DB.Integer, primary_key=True)
    title = DB.Column(DB.String, nullable=False)
    question = DB.Column(DB.String, nullable=False)
    answer = DB.Column(DB.String, nullable=False)
    #distractors = DB.relationship('Distractor', backref='quiz', lazy=True)
    def __repr__(self):
        return "Quiz(id='%d',title='%s',question='%s',solution='%s')" % (self.id, self.title, self.question, self.answer)


class Distractor(DB.Model):
    __tablename__ = 'distractors'
    id = DB.Column(DB.Integer, primary_key=True)
    quiz_id = DB.Column(None, DB.ForeignKey('quizzes.id'))
    answer = DB.Column(DB.String, nullable=False)
    def __repr__(self):
        return "Quiz(quiz_id=%d,id='%d',answer='%s')" % (self.quiz_id, self.id, self.answer)
