# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from evopie.datastore import DataStore
from evopie import APP
import evopie.models as models

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
    #NOTE HTML5 forms can not submit a PUT (only POST), so we reject any non-json request
    if not request.json:
        abort(406) # not acceptable

    title = request.json['title']
    question = request.json['question']
    answer = request.json['answer']
    
    if answer == None or question == None or title == None:
        abort(400) # bad request
    
    success = DS.update_question(question_id, title, question, answer)
    
    if success:
        return Response('{"status" : "Question updated in database"}', status=200, mimetype='application/json')
    else:
        return Response('{"status" : "Question NOT updated in database"}', status=404, mimetype='application/json')




@APP.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    '''
    Delete given question.
    '''
    q = models.Question.query.get_or_404(question_id)
    models.DB.session.delete(q)
    models.DB.session.commit()
    response = ('Question Deleted from database', 200, {"Content-Type": "application/json"})
    return make_response(response)

    

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



#NOTE Using index for distractors, relative to question, rather than their IDs.
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
    d = DS.get_distractor_for_question(question_id, distractor_index)
    models.DB.session.delete(d)
    models.DB.session.commit()
    response = ('Distractor Deleted from database', 200, {"Content-Type": "application/json"})
    return make_response(response)



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
    d = models.Distractor.query.get_or_404(distractor_id)
    models.DB.session.delete(d)
    models.DB.session.commit()
    response = ('Distractor Deleted from database', 200, {"Content-Type": "application/json"})
    return make_response(response)



@APP.route('/quizquestions', methods=['GET'])
def get_all_quiz_questions():
    '''
    Get, in JSON format, all the QuizQuestions from the database.
    '''
    return jsonify(DS.get_all_quiz_questions_json())



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
        # so, instead, we restrict ourselves to only the JSON format, for now at least.

    if DS.add_quiz_question(question_id, distractors_ids):
        return Response('{"status" : "QuizQuestion added to data base"}', status=201, mimetype='application/json')
    else:
        abort(400) # bad request
    


@APP.route('/quizquestions/<int:qq_id>', methods=['GET', 'PUT', 'DELETE'])
def quiz_questions(qq_id):
    '''
    Handles requests on a specific QuizQuestion
    '''
    
    #making sure the QuizQuestion exists
    qq = DS.get_quiz_question(qq_id)
    if qq == None:
        abort(404)
    
    if request.method == 'GET':
        return jsonify(DS.get_quiz_question_json(qq_id))
    elif request.method == 'PUT':
        if not request.json:
            abort(406) # not acceptable
        else:
            #TODO implement PUT on QuizQuestions; how do we handle the update of a variable number of distractors?
            # Extracting data from request
            # ... = request.json['...']
            # Making sure all fields were there 
            # Also make sure all distractors refer to actual distractors in the DB
            # if ... == None:
            abort(400) # bad request
            #else:
            # update the distractors on our object
            # qq.distractors = ...
            # commit changes to DB via ORM
            #models.session.commit()
    elif request.method == 'DELETE':
        models.DB.session.delete(qq)
        models.DB.session.commit()
        response = ('Quiz Question Deleted from database', 200, {"Content-Type": "application/json"})
        #NOTE the above is a bloody tuple, not 3 separate parameters to make_response
        return make_response(response)
    else:
        abort(406) # not acceptable; should never trigger based on @APP.route
    
