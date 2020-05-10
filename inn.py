#this is an inn, aka a rest server ;p

#!flask/bin/python
from flask import Flask, jsonify, abort
from random import shuffle # to shuffle lists
from datastore import DataStore, Quiz, Distractor

DS = DataStore()
app = Flask(__name__)



@app.route('/')
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



"""
@app.route('/q/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    q = None
    quizzes = DS.get_all_quizzes()
    distractors = DS.get_all_distractors()
    for it in quizzes:
        if it.id == quiz_id:
            q = it.copy()
    dists = distractors[quiz_id]
    q['options'] = []
    q['options'].append(q['answer'])
    del q['answer']
    n=1
    for d in dists:
        q['options'].append(d)
        n += 1
    return jsonify(q)


@app.route('/q/<int:quiz_id>', methods=['POST'])
def post_quiz_distractor(quiz_id):
    '''add a distractor to the specified quiz'''
    distractors = DS.get_all_distractors()
    new_distractor = u'Something, Something... Something'
    dists = distractors[quiz_id]
    #DS.add_distractor(quiz_id, new_distractor)
    dists.append(new_distractor)
"""


if __name__ == '__main__':
    app.run(debug=True)
