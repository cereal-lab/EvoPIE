#this is an inn, aka a rest server ;p
from flask import jsonify
from random import shuffle # to shuffle lists
from datastore import DataStore, APP

DS = DataStore()


@APP.route('/')
def index():
    output = ""
    quizzes = DS.get_all_quizzes()
    distractors = DS.get_all_distractors()
    
    for q in quizzes:
        output += u'<h1>' + q.title + u'</h1>'
        output += u'<p>' + q.question + u'</p>'
        options = []
        for d in distractors:
            if d.quiz_id == q.id:
                options.append(d.answer)    
        options.append(q.answer)
        shuffle(options)
        output += u'<ul>' 
        for o in options:
            output += u'<li>' + o + u'</li>' 
        output += u"</ul>"       
    return output



@APP.route('/q/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    q = DS.get_full_quiz(quiz_id)
    return jsonify(q)


"""
@APP.route('/q/<int:quiz_id>', methods=['POST'])
def post_quiz_distractor(quiz_id):
    '''add a distractor to the specified quiz'''
    distractors = DS.get_all_distractors()
    new_distractor = u'Something, Something... Something'
    dists = distractors[quiz_id]
    #DS.add_distractor(quiz_id, new_distractor)
    dists.append(new_distractor)
"""


if __name__ == '__main__':
    APP.run(debug=True)
