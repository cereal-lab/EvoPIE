# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response

from random import shuffle # to shuffle lists

from evopie import APP
import evopie.models as models



@APP.route('/')
def index():
    '''
    index page for the whole thing; use to test out a rudimentary user interface
    '''
    all = models.Question.query.all()
    result =  [q.dump_as_dict() for q in all]
    return render_template('index.html', quizzes=result)



@APP.route('/questions', methods=['GET'])
def get_all_questions():
    '''
    Get, in JSON format, all the questions from the database,
    including all its distractors.
    '''
    all = models.Question.query.all()
    result = [q.dump_as_dict() for q in all]
    return jsonify(result)



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
    
    q = models.Question(title=title, question=question, answer=answer)
    models.DB.session.add(q)
    models.DB.session.commit()

    if request.json:
        response = ('Question & answer added to database', 201, {"Content-Type": "application/json"})
        return make_response(response)
    else:
        return redirect(url_for('index'))

    

@APP.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    '''
    Get, in JSON format, a specified question from the database,
    including all its distractors.
    The fact that all distractors are included is the main difference
    between Question and QuizQuestion.
    Answer and distractors are shuffled together as options from which
    the student will have to pick.
    '''
    q = models.Question.query.get_or_404(question_id)
    return jsonify(q.dump_as_dict())



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
    
    q = models.Question.query.get_or_404(question_id)
    #TODO only assign the fields that were not None in the request
    #NOTE are they even None at some point; e.g., instead of empty strings?
    q.title = title
    q.question = question
    q.answer = answer
    models.DB.session.commit()
    response = ('Distractor updated in database', 204, {"Content-Type": "application/json"})
    return make_response(response)



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
    q = models.Question.query.get_or_404(question_id)
    result = [d.dump_as_dict() for d in q.distractors]
    return jsonify(result)
    


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
    
    q = models.Question.query.get_or_404(question_id)
    q.distractors.append(models.Distractor(answer=answer,question_id=q.id))
    models.DB.session.commit()
    if request.json:
        response = ('Distractor added to Question in database', 201, {"Content-Type": "application/json"})
        return make_response(response)
    else:
        return redirect(url_for('index'))
        #TODO how to handle error in a non-REST client?



#NOTE Using index for distractors, relative to question, rather than their IDs.
# Please note that, in the next 3 routes, the distractor is identified by its index
# in the list of distractors for this question, instead of using its distractor ID.
# Assuming here that the queries from the DB will be idempotent
# with respect to the ordering of the distractors.
# The caller must also display them to the user in the same order.
# Probably something to keep an eye on and eventually fix...



@APP.route('/questions/<int:question_id>/distractors/<int:distractor_index>', methods=['GET'])
def get_distractor_for_question(question_id, distractor_index):
    all = models.Question.query.get_or_404(question_id).distractors
    if len(all) <= distractor_index or distractor_index < 0:
        abort(406)
    return jsonify(all[distractor_index].dump_as_dict())
    


@APP.route('/questions/<int:question_id>/distractors/<int:distractor_index>', methods=['PUT'])
def put_distractor_for_question(question_id, distractor_index):
    if not request.json:
        abort(406) # not acceptable
    
    answer = request.json['answer']
    if answer == None:
        abort(400) # bad request
    
    q = models.Question.query.get_or_404(question_id)
    d = q.distractors[distractor_index]
    d.answer = answer
    models.DB.session.commit()
    response = ('Distractor updated in database', 204, {"Content-Type": "application/json"})
    return make_response(response)



@APP.route('/questions/<int:question_id>/distractors/<int:distractor_index>', methods=['DELETE'])
def delete_distractor_for_question(question_id, distractor_index):
    '''
    Delete given distractor.
    '''
    q = models.Question.query.get_or_404(question_id)
    d = q.distractors[distractor_index]
    models.DB.session.delete(d)
    models.DB.session.commit()
    response = ('Distractor Deleted from database', 204, {"Content-Type": "application/json"})
    return make_response(response)



# In the following routes, we are accessing distractors by their unique IDs



@APP.route('/distractors/<int:distractor_id>', methods=['GET'])
def get_distractor(distractor_id):
    d = models.Distractor.query.get_or_404(distractor_id)
    return jsonify({ "answer": d.answer })



@APP.route('/distractors/<int:distractor_id>', methods=['PUT'])
def put_distractor(distractor_id):
    if not request.json:
        abort(406) # not acceptable
    else:
        answer = request.json['answer']    
        if answer == None:
            abort(400) # bad request
    
    d = models.Distractor.query.get_or_404(distractor_id)
    d.answer = answer
    models.DB.session.commit()
    response = ('Distractor updated in database', 204, {"Content-Type": "application/json"})
    return make_response(response)
    
    

@APP.route('/distractors/<int:distractor_id>', methods=['DELETE'])
def delete_distractor(distractor_id):
    '''
    Delete given distractor.
    '''
    d = models.Distractor.query.get_or_404(distractor_id)
    models.DB.session.delete(d)
    models.DB.session.commit()
    response = ('Distractor Deleted from database', 204, {"Content-Type": "application/json"})
    return make_response(response)



@APP.route('/quizquestions', methods=['GET'])
def get_all_quiz_questions():
    '''
    Get, in JSON format, all the QuizQuestions from the database.
    '''
    all = models.QuizQuestion.query.all()
    result = [q.dump_as_dict() for q in all]
    return jsonify(result)



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

    q = models.Question.query.get_or_404(question_id)
    qq = models.QuizQuestion(question=q)
    distractors = [models.Distractor.query.get_or_404(id) for id in distractors_ids]
    
    for d in distractors:
        qq.distractors.append(d)
    
    models.DB.session.add(qq)
    models.DB.session.commit()

    response = ('Quiz Question added to database', 201, {"Content-Type": "application/json"})
    return make_response(response)
    


@APP.route('/quizquestions/<int:qq_id>', methods=['GET', 'PUT', 'DELETE'])
def quiz_questions(qq_id):
    '''
    Handles requests on a specific QuizQuestion
    '''
    
    #making sure the QuizQuestion exists
    qq = models.QuizQuestion.query.get_or_404(qq_id)
    
    if request.method == 'GET':
        return jsonify(qq.dump_as_dict())
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
        response = ('Quiz Question Deleted from database', 204, {"Content-Type": "application/json"})
        #NOTE the above is a bloody tuple, not 3 separate parameters to make_response
        return make_response(response)
    else:
        abort(406) # not acceptable; should never trigger based on @APP.route
    

