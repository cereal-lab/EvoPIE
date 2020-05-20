#this is an inn, aka a rest server ;p
from flask import jsonify, abort, request, Response, render_template, redirect, url_for
from datastore import DataStore, APP

DS = DataStore()

@APP.route('/')
def index():
    quizzes = DS.get_all_questions_json()
    return render_template('index.html', quizzes=quizzes)


@APP.route('/q/<int:question_id>', methods=['GET'])
def get_quiz(question_id):
    q = DS.get_question_json(question_id)
    if q == None:
        abort(404)
    return jsonify(q)


@APP.route('/q/<int:question_id>', methods=['POST'])
def post_quiz_distractor(question_id):
    '''add a distractor to the specified quiz'''
    if request.json:
        answer = request.json['answer']
    else:
        answer = request.form['answer']
    
    if answer == None:
        abort(400) # bad request
    
    result = DS.get_question(question_id)
    if result == None: 
        abort(404) # not found

    DS.add_distractor_for_question(question_id, answer)
    
    if request.json:
        return Response('{"status" : "Distractor answer added to quiz"}', status=201, mimetype='application/json')
    else:
        return redirect(url_for('index'))


if __name__ == '__main__':
    # to recreate the DB;
    # rm the DB file
    # pipenv run python
    # import datastore
    # ds = datastore.DataStore()
    # ds.populate()
    DS.populate()
    APP.run(debug=True)