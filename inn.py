#this is an inn, aka a rest server ;p
from flask import jsonify, abort, request, Response
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
    if q == None: 
        abort(404)
    return jsonify(q)



@APP.route('/q/<int:quiz_id>', methods=['POST'])
def post_quiz_distractor(quiz_id):
    '''add a distractor to the specified quiz'''
    #if not request.json or not 'title' in request.json:
    #    abort(400)
    answer = request.json['answer']
    if answer == None:
        abort(400) # bad request
    
    result = DS.add_distractor_for_quiz(quiz_id, answer)
    if result == None: 
        abort(404) # not found

    return Response('{"status" : "Distractor answer added to quiz"}', status=201, mimetype='application/json')



if __name__ == '__main__':
    #drop all tables the populate with testing data
    #DS.drop_all()
    DS.populate()
    APP.run(debug=True)
