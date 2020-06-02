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
        stem = request.json['stem']
        answer = request.json['answer']
    else:
        title = request.form['title']
        stem = request.form['stem']
        answer = request.form['answer']
    
    if answer == None or stem == None or title == None:
        abort(400) # bad request
    
    q = models.Question(title=title, stem=stem, answer=answer)
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
    Answer and distractors are shuffled together as alternatives from which
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
    stem = request.json['stem']
    answer = request.json['answer']
    
    if answer == None or stem == None or title == None:
        abort(400) # bad request
    
    q = models.Question.query.get_or_404(question_id)
    #TODO only assign the fields that were not None in the request
    #NOTE are they even None at some point; e.g., instead of empty strings?
    q.title = title
    q.stem = stem
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
        distractors_ids = [did for did in request.json['distractors_ids']]
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
def ALL_quiz_questions(qq_id):
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
            distractors_ids = []
            if request.json:
                question_id = request.json['qid']
                distractors_ids = [did for did in request.json['distractors_ids']]
            else:
                abort(406) # not acceptable
            
            q = models.Question.query.get_or_404(question_id)
            qq.question = q
            distractors = [models.Distractor.query.get_or_404(id) for id in distractors_ids]
    
            for d in distractors:
                qq.distractors.append(d)
    
            models.DB.session.add(qq)
            models.DB.session.commit()

            response = ('Quiz Question updated in database', 201, {"Content-Type": "application/json"})
            return make_response(response)

    elif request.method == 'DELETE':
        models.DB.session.delete(qq)
        models.DB.session.commit()
        response = ('Quiz Question Deleted from database', 204, {"Content-Type": "application/json"})
        #NOTE the above is a bloody tuple, not 3 separate parameters to make_response
        return make_response(response)
    else:
        abort(406) # not acceptable; should never trigger based on @APP.route



@APP.route('/quizzes', methods=['POST'])
def post_new_quiz():
    '''
    Create a new quiz
    '''
    title = request.json['title']
    description = request.json['description']

    q = models.Quiz(title=title, description=description)
    
    # Adding the questions, based on the questions_id submitted
    for qid in request.json['questions_ids']:
        question = models.QuizQuestion.query.get_or_404(qid)
        q.quiz_questions.append(question)
    
    # There should be no quiz attempts for us to add at this point
    # q.quiz_attempts.append()
    
    models.DB.session.add(q)
    models.DB.session.commit()

    response = ('Quiz added to database', 201, {"Content-Type": "application/json"})
    return make_response(response)



@APP.route('/quizzes', methods=['GET'])
def get_all_quizzes():
    '''
    Get us all quizzes, for debugging purposes
    '''
    quizzes = models.Quiz.query.all()
    return jsonify([q.dump_as_dict()for q in quizzes])



@APP.route('/quizzes/<int:qid>', methods=['GET', 'PUT', 'DELETE'])
def ALL_quizzes(qid):
    '''
    Handles all accepted requests on a specific QuizQuestion
    '''
    quiz = models.Quiz.query.get_or_404(qid)
    
    if request.method == 'GET':
        return jsonify(quiz.dump_as_dict())
    elif request.method == 'PUT':
        if not request.json:
            abort(406) # not acceptable
        else:
            quiz.title = request.json['title']
            quiz.description = request.json['description']
            quiz.quiz_questions = []
            for qid in request.json['questions_ids']:
                question = models.QuizQuestion.query.get_or_404(qid)
                quiz.quiz_questions.append(question)
            models.DB.session.commit()
            response = ('Quiz updated in database', 204, {"Content-Type": "application/json"})
            return make_response(response)
    elif request.method == 'DELETE':
        models.DB.session.delete(quiz)
        models.DB.session.commit()
        response = ('Quiz deleted from database', 204, {"Content-Type": "application/json"})
        return make_response(response)
    else:
        abort(406) # not acceptable; should never trigger based on @APP.route



@APP.route('/quizzes/<int:qid>/take', methods=['GET', 'POST'])
def ALL_quizzes_take(qid):
    '''
    Take the quiz and post the answers / justifications
    '''
    quiz = models.Quiz.query.get_or_404(qid)
    
    #TODO ensure that authenticated student user is assigned this quiz
    
    if request.method == 'GET':
        return jsonify(quiz.dump_as_dict())
    elif request.method == 'POST':
        if not request.json:
            abort(406) # not acceptable
        else:
            #TODO check if len(responses) == len(justifications) == len(quiz.quiz_questions)
            r = models.QuizAttempt(quiz_id=quiz.id)
            r.initial_responses = str(request.json['initial_responses']) # extract dictionary of question_id : distractor_ID (or none if correct answer)

            #TODO take into consideration what mode was set by instructor; regular quiz vs. peer instruction quiz
            r.justifications = str(request.json['justifications']) # same structure here; distractor_ID : justification
            #TODO set the student_id / timestamps / ... fields
            #TODO do we compute the initial score
            r.initial_scores = ""

            #TODO validate the quiz attempt;
            # make sure that the student has been assigned this quiz
            # check the due dates for too early / too late
            # check the max duration
            # If answers have already been submitted, accept edits only until due date.

            models.DB.session.add(r)
            models.DB.session.commit()

            response     = ('Quiz attempt recorded in database', 204, {"Content-Type": "application/json"})
            return make_response(response)



@APP.route('/quizzes/<int:qid>/review', methods=['GET', 'POST'])
def ALL_quizzes_review(qid):
    '''
    Re-take the quiz with peers' answers and justifications
    '''
    pass #TODO
    # GET	get the quiz data for client to administer to students
    #       including answers + justifications of two other students.
    # POST	submit the answers to all questions; no justification needed, regardless of quiz mode
    #       Select one of the two students whose answers + justifications were seen as the most useful
    #       Specify which of their justification was the most conductive to learning something.
