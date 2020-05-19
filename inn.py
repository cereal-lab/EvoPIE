#this is an inn, aka a rest server ;p
from flask import jsonify, abort, request, Response, render_template
from datastore import DataStore, APP

DS = DataStore()


@APP.route('/')
def index():
    quizzes = DS.get_all_full_quizzes()
    return render_template('index.html', quizzes=quizzes)



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
    if request.json:
        answer = request.json['answer']
    else:
        answer = request.form['answer']
    
    if answer == None:
        abort(400) # bad request
    
    result = DS.get_quiz(quiz_id)
    if result == None: 
        abort(404) # not found
    DS.add_distractor_for_quiz(quiz_id, answer)
    return Response('{"status" : "Distractor answer added to quiz"}', status=201, mimetype='application/json')



if __name__ == '__main__':
    # to recreate the DB;
    # rm the DB file
    # pipenv run python
    # import datastore
    # ds = datastore.DataStore()
    # ds.populate()
    DS.populate()
    APP.run(debug=True)
