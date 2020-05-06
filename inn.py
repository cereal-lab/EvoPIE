#this is an inn, aka a rest server ;p

#!flask/bin/python
from flask import Flask, jsonify, abort

import random # for shuffle(list)

#list of quizzes, each represented as a dictionary
quizzes = [
    {
        'id': 1,
        'title': u'Sir Lancelot and the bridge keeper, part 1',
        'question': u'What... is your name?', 
        'answer': u'Sir Lancelot of Camelot'
    },
    {
        'id': 2,
        'title': u'Sir Lancelot and the bridge keeper, part 2',
        'question': u'What... is your quest?', 
        'answer': u'To seek the holy grail'
    },
    {
        'id': 3,
        'title': u'Sir Lancelot and the bridge keeper, part 3',
        'question': u'What... is your favorite colour?', 
        'answer': u'Blue'
    }
]

# distractors are keyed by the ID of the quiz for which they
# are meant
# each value is a list of all distractors for that quiz_id
distractors = {
    1: [ u'Sir Galahad of Camelot',
         u'Sir Arthur of Camelot',
         u'Sir Bevedere of Camelot',
         u'Sir Robin of Camelot'
        ],
    2: [ u'To bravely run away',
         u'To spank Zoot',
         u'To find a shrubbery'
        ],
    3: [ u'Green', u'Red', u'Yellow'
        ]
}

# http://montypython.50webs.com/scripts/Holy_Grail/Scene22.htm
app = Flask(__name__)

@app.route('/')
def index():
    output = ""
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
    # add a distractor to this quiz
    new_distractor = u'Something, Something... Something'
    dists = distractors[quiz_id]
    dists.append(new_distractor)



if __name__ == '__main__':
    app.run(debug=True)
    
    
    


