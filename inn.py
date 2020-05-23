#this is an inn, aka a rest server ;p
from flask import jsonify, abort, request, Response, render_template, redirect, url_for
from datastore import DataStore, APP

DS = DataStore()

@APP.route('/')
def index():
    '''
    index page for the whole thing; use to test out a rudimentary user interface
    '''
    quizzes = DS.get_all_questions_json()
    return render_template('index.html', quizzes=quizzes)


@APP.route('/questions', methods=['GET'])
def get_all_questions():
    '''
    Get, in JSON format, all the questions from the database,
    including all its distractors.
    '''
    q = DS.get_all_questions_json()
    return jsonify(q)


@APP.route('/questions', methods=['POST'])
def post_new_question():
    '''
    Add a question and its answer to the database.
    '''
    if request.json:
        title = request.json['title']
        question = request.json['question']
        answer = request.json['answer']
    else:
        title = request.form['title']
        question = request.form['question']
        answer = request.form['answer']
    
    if answer == None or question == None:
        abort(400) # bad request
    
    DS.add_question(title, question, answer)
    
    if request.json:
        return Response('{"status" : "Question and answer added to database"}', status=201, mimetype='application/json')
    else:
        return redirect(url_for('index'))

    

    
@APP.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    '''
    Get, in JSON format, a specified question from the database,
    including all its distractors.
    '''
    q = DS.get_question_json(question_id)
    if q == None:
        abort(404)
    return jsonify(q)



@APP.route('/questions/<int:question_id>', methods=['PUT'])
def put_question(question_id):
    '''
    Update a given question.
    '''
    #TODO
    q = DS.get_question_json(question_id)
    if q == None:
        abort(404)
    return jsonify(q)
    
    

@APP.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    '''
    Delete given question.
    '''
    q = DS.get_question_json(question_id)
    if q == None:
        abort(404)
    DS.delete_question(question_id)
    response = jsonify(success=True)
    response.status_code=200
    return response


@APP.route('/questions/<int:question_id>/distractors', methods=['POST'])
def post_question_distractor(question_id):
    '''
    Add a distractor to the specified question.
    '''
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
        return Response('{"status" : "Distractor answer added to question in data base"}', status=201, mimetype='application/json')
    else:
        return redirect(url_for('index'))



@APP.route('/questions/<int:question_id>/distractors/<int:distractor_id>', methods=['GET'])
def get_question_distractor(question_id, distractor_id):
    #TODO
    return redirect(url_for('index'))



@APP.route('/questions/<int:question_id>/distractors/<int:distractor_id>', methods=['PUT'])
def put_question_distractor(question_id, distractor_id):
    #TODO
    return redirect(url_for('index'))



@APP.route('/questions/<int:question_id>/distractors/<int:distractor_id>', methods=['DELETE'])
def delete_question_distractor(question_id, distractor_id):
    return redirect(url_for('index'))



if __name__ == '__main__':
    # to recreate the DB;
    # rm the DB file
    # pipenv run python
    # import datastore
    # ds = datastore.DataStore()
    # ds.populate()
    
    #lets populate by using a script sending data with curl instead
    # so we test out that our RESTful API is working
    # DS.populate()
    APP.run(debug=True)