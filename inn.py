#this is an inn, aka a rest server ;p

#!flask/bin/python
from flask import Flask, jsonify, abort

import random # for shuffle(list)
from datastore import DataStore

DS = DataStore('sqlite', dbname='quizlib.sqlite')

# http://montypython.50webs.com/scripts/Holy_Grail/Scene22.htm
app = Flask(__name__)

@app.route('/')
def index():
    output = ""
    quizzes = DS.get_all_quizzes()
    distractors = DS.get_all_distractors()
    for q in quizzes:
        output += u'<h1>' + q['title'] + u'</h1>'
        output += u'<p>' + q['question'] + u'</p>'
        dists = distractors[ q['id'] ].copy()
        dists.append(q['answer'])
        random.shuffle(dists)
        output += u'<ul>' 
        for d in dists:
            output += u'<li>' + d + u'</li>' 
        output += u"</ul>"       
    return output



@app.route('/q/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    q = None
    quizzes = DS.get_all_quizzes()
    distractors = DS.get_all_distractors()
    for it in quizzes:
        if it['id'] == quiz_id:
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
    DS.add_distractor(quiz_id, new_distractor)
    dists.append(new_distractor)



if __name__ == '__main__':
    app.run(debug=True)
    
    
    


