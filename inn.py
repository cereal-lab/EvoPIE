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
    
    if answer == None or question == None or title == None:
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
    #FIXME note that HTML5 will not allow a form to submit a PUT instead of a POST
    # so we need to clean up the code in here accordingly...
    if request.json:
        title = request.json['title']
        question = request.json['question']
        answer = request.json['answer']
    else:
        title = request.form['title']
        question = request.form['question']
        answer = request.form['answer']
    
    if answer == None or question == None or title == None:
        abort(400) # bad request
    
    success = DS.update_question(question_id, title, question, answer)
    
    if request.json:
        if success:
            return Response('{"status" : "Question updated in database"}', status=200, mimetype='application/json')
        else:
            return Response('{"status" : "Question NOT updated in database"}', status=404, mimetype='application/json')
    else:
        return redirect(url_for('index'))

    

@APP.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    '''
    Delete given question.
    '''
    if DS.delete_question(question_id):
        return Response('{"status" : "Question deleted from database"}', status=200, mimetype='application/json')
    else:
        abort(404)



@APP.route('/questions/<int:question_id>/distractors', methods=['GET'])
def get_distractors_for_question(question_id):
    '''
    Get all distractors for the specified question.
    '''
    q = DS.get_distractors_for_question_json(question_id)
    if q == None:
        abort(404)
    else:
        return jsonify(q)
    


@APP.route('/questions/<int:question_id>/distractors', methods=['POST'])
def post_new_distractor_for_question(question_id):
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



#FIXME
# Please note that, in the next 3 routes, the distractor is identified by its index
# in the list of distractors for this question, instead of using its distractor ID.
# Assuming here that the queries from the DB will be idempotent
# with respect to the ordering of the distractors.
# The caller must also display them to the user in the same order.
# Probably something to keep an eye on and eventually fix...



@APP.route('/questions/<int:question_id>/distractors/<int:distractor_index>', methods=['GET'])
def get_distractor_for_question(question_id, distractor_index):
    d = DS.get_distractor_for_question_json(question_id, distractor_index)
    if d == None:
        abort(404)
    else:
        return jsonify(d)



@APP.route('/questions/<int:question_id>/distractors/<int:distractor_index>', methods=['PUT'])
def put_distractor_for_question(question_id, distractor_index):
    if not request.json:
        abort(406) # not acceptable
    
    answer = request.json['answer']
    
    if answer == None:
        abort(400) # bad request
    
    success = DS.update_distractor_for_question(question_id, distractor_index, answer)
    
    if success:
        return Response('{"status" : "Distractor updated in database"}', status=200, mimetype='application/json')
    else:
        return Response('{"status" : "Distractor NOT updated in database"}', status=404, mimetype='application/json')



@APP.route('/questions/<int:question_id>/distractors/<int:distractor_index>', methods=['DELETE'])
def delete_distractor_for_question(question_id, distractor_index):
    '''
    Delete given distractor.
    '''
    if DS.delete_distractor_for_question(question_id, distractor_index):
        return Response('{"status" : "Distractor deleted from database"}', status=200, mimetype='application/json')
    else:
        abort(404)



# In the following routes, we are accessing distractors by their unique IDs



@APP.route('/distractors/<int:distractor_id>', methods=['GET'])
def get_distractor(distractor_id):
    d = DS.get_distractor_json(distractor_id)
    if d == None:
        abort(404)
    else:
        return jsonify(d)



@APP.route('/distractors/<int:distractor_id>', methods=['PUT'])
def put_distractor(distractor_id):
    if not request.json:
        abort(406) # not acceptable
    else:
        answer = request.json['answer']
    
    if answer == None:
        abort(400) # bad request
    
    success = DS.update_distractor(distractor_id, answer)
    
    if success:
        return Response('{"status" : "Distractor updated in database"}', status=200, mimetype='application/json')
    else:
        return Response('{"status" : "Distractor NOT updated in database"}', status=404, mimetype='application/json')



@APP.route('/distractors/<int:distractor_id>', methods=['DELETE'])
def delete_distractor(distractor_id):
    '''
    Delete given distractor.
    '''
    if DS.delete_distractor(distractor_id):
        return Response('{"status" : "Distractor deleted from database"}', status=200, mimetype='application/json')
    else:
        abort(404)



@APP.route('/quizquestions', methods=['GET'])
def get_all_quiz_questions():
    '''
    Get, in JSON format, all the QuizQuestions from the database.
    '''
    q = DS.get_all_quiz_questions_json()
    return jsonify(q)



@APP.route('/quizquestions', methods=['POST'])
def post_new_quiz_question():
    '''
    Add a QuizQuestion.
    '''
    distractors_ids = []
    if request.json:
        question_id = request.json['qid']
        distractors_ids.append(request.json['d1'])
        distractors_ids.append(request.json['d2'])
        distractors_ids.append(request.json['d3'])
    else:
        abort(406) # not acceptable
        #FIXME we have been redirecting for posts from forms, but this does not allow to handle errors statuses.
        # so, instead, we restrict ourselves to only the JSON format, or now at least.

    if DS.add_quiz_question(question_id, distractors_ids):
        return Response('{"status" : "QuizQuestion added to data base"}', status=201, mimetype='application/json')
    else:
        abort(400) # bad request
    


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