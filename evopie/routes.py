# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from flask_login import login_required, current_user

from random import shuffle

from evopie import APP
import evopie.models as models
    
    

@APP.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.first_name)



@APP.route('/')
def index():
    '''
    Index page for the whole thing; used to test out a rudimentary user interface
    '''
    all_quizzes =  [q.dump_as_dict() for q in models.Question.query.all()]
    return render_template('index.html', quizzes=all_quizzes)



@APP.route('/questions', methods=['GET'])
def get_all_questions():
    '''
    Get, in JSON format, all the questions from the database,
    including, for each, all its distractors.
    '''
    all_questions = [q.dump_as_dict() for q in models.Question.query.all()]
    return jsonify(all_questions)



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
        #FIXME do we want to continue handling both formats?
        title = request.form['title']
        stem = request.form['stem']
        answer = request.form['answer']

    # validate that all required information was sent
    if answer is None or stem is None or title is None:
        abort(400, "Unable to create new question due to missing data") # bad request
    
    q = models.Question(title=title, stem=stem, answer=answer)
    models.DB.session.add(q)
    models.DB.session.commit()

    if request.json:
        response = ('Question & answer added to database', 201, {"Content-Type": "application/json"})
        return make_response(response)
    else:
        return redirect(url_for('dashboard'))

    

@APP.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    '''
    Get, in JSON format, a specified question from the database,
    including all its distractors.
    The fact that *all* of the distractors are included is the main difference
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
        abort(406, "JSON format required for request") # not acceptable

    title = request.json['title']
    stem = request.json['stem']
    answer = request.json['answer']
    
    # validate that all required information was sent
    if answer is None or stem is None or title is None:
        abort(400, "Unable to modify question due to missing data") # bad request
    
    q = models.Question.query.get_or_404(question_id)
    #TODO only assign the fields that were not None in the request
    #NOTE are they even None at some point; e.g., instead of empty strings?
    q.title = title
    q.stem = stem
    q.answer = answer
    models.DB.session.commit()
    response = ('Question updated in database', 200, {"Content-Type": "application/json"})
    #NOTE should it be 204? probably but I prefer to return a message so that CURL displays something indicating that the operation succeeded
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
    
    # validate that all required information was sent
    if answer is None:
        abort(400, "Unable to create new distractor due to missing data") # bad request
    
    q = models.Question.query.get_or_404(question_id)
    q.distractors.append(models.Distractor(answer=answer,question_id=q.id))
    models.DB.session.commit()
    
    if request.json:
        response = ('Distractor added to Question in database', 201, {"Content-Type": "application/json"})
        return make_response(response)
    else:
        return redirect(url_for('dashboard'))
        #TODO how to handle error in a non-REST client? e.g., flash an error message then redirect?



@APP.route('/distractors/<int:distractor_id>', methods=['GET'])
def get_distractor(distractor_id):
    d = models.Distractor.query.get_or_404(distractor_id)
    return jsonify({ "answer": d.answer })



@APP.route('/distractors/<int:distractor_id>', methods=['PUT'])
def put_distractor(distractor_id):
    if not request.json:
        abort(406, "JSON format required for request") # not acceptable
    
    answer = request.json['answer']    
    
    # validate that all required information was sent
    if answer is None:
        abort(400, "Unable to modify distractor due to missing data") # bad request

    d = models.Distractor.query.get_or_404(distractor_id)
    d.answer = answer
    models.DB.session.commit()

    response = ('Distractor updated in database', 200, {"Content-Type": "application/json"})
    #NOTE see previous note about using 204 vs 200
    return make_response(response)



@APP.route('/distractors/<int:distractor_id>', methods=['DELETE'])
def delete_distractor(distractor_id):
    '''
    Delete given distractor.
    '''
    d = models.Distractor.query.get_or_404(distractor_id)
    models.DB.session.delete(d)
    models.DB.session.commit()
    response = ('Distractor deleted from database', 204, {"Content-Type": "application/json"})
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
    if not request.json:
        abort(406, "JSON format required for request") # not acceptable
        
    question_id = request.json['qid']

    # validate that all required information was sent
    if question_id is None or request.json['distractors_ids'] is None:
        abort(400, "Unable to create new quiz question due to missing data") # bad request
    distractors_ids = [did for did in request.json['distractors_ids']]
    
    q = models.Question.query.get_or_404(question_id)
    qq = models.QuizQuestion(question=q)
    distractors = [models.Distractor.query.get_or_404(id) for id in distractors_ids]
    #TODO verify that distractors belong to that question
    #TODO verify that distractors are also all different
    
    for d in distractors:
        qq.distractors.append(d)
    
    models.DB.session.add(qq)
    models.DB.session.commit()

    response = ('Quiz Question added to database', 201, {"Content-Type": "application/json"})
    return make_response(response)



@APP.route('/quizquestions/<int:qq_id>', methods=['GET'])
def get_quiz_questions(qq_id):
    '''
    Handles GET requests on a specific QuizQuestion
    '''
    qq = models.QuizQuestion.query.get_or_404(qq_id)
    return jsonify(qq.dump_as_dict())



@APP.route('/quizquestions/<int:qq_id>', methods=['DELETE'])
def delete_quiz_questions(qq_id):
    '''
    Handles DELETE requests on a specific QuizQuestion
    '''
    qq = models.QuizQuestion.query.get_or_404(qq_id)
    models.DB.session.delete(qq)
    models.DB.session.commit()
    response = ('Quiz Question Deleted from database', 200, {"Content-Type": "application/json"})
    #NOTE see previous note about using 204 vs 200
    #NOTE the above is a bloody tuple, not 3 separate parameters to make_response
    return make_response(response)



@APP.route('/quizquestions/<int:qq_id>', methods=['PUT'])
def put_quiz_questions(qq_id):
    '''
    Handles PUT requests on a specific QuizQuestion
    '''
    qq = models.QuizQuestion.query.get_or_404(qq_id)
    
    if not request.json:
        abort(406, "JSON format required for request") # not acceptable

    # validate that all required information was sent
    if request.json['qid'] is None or request.json['distractors_ids'] is None:
        abort(400, "Unable to modify quiz question due to missing data") # bad request

    question_id = request.json['qid']
    distractors_ids = [did for did in request.json['distractors_ids']]

    qq.question = models.Question.query.get_or_404(question_id)
    distractors = [models.Distractor.query.get_or_404(id) for id in distractors_ids]

    #BUG we are adding distractors not replacing them. Checked for multiple occurences of this bug in all put_* methods;
    #for d in distractors:
    #    qq.distractors.append(d)
    qq.distractors = distractors
    #BUG models.DB.session.add(qq)
    models.DB.session.commit()

    response = ('Quiz Question updated in database', 201, {"Content-Type": "application/json"})
    return make_response(response)



@APP.route('/quizzes', methods=['POST'])
def post_new_quiz():
    '''
    Create a new quiz
    '''
    title = request.json['title']
    description = request.json['description']

    # validate that all required information was sent
    if title is None or description is None:
        abort(400, "Unable to create new quiz due to missing data") # bad request

    if request.json['questions_ids'] is None:
        abort(400, "Unable to create new quiz due to missing data") # bad request
    
    q = models.Quiz(title=title, description=description)
    
    # Adding the questions, based on the questions_id that were submitted
    for qid in request.json['questions_ids']:
        question = models.QuizQuestion.query.get_or_404(qid)
        q.quiz_questions.append(question)
    
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



@APP.route('/quizzes/<int:qid>', methods=['GET'])
def get_quizzes(qid):
    '''
    Handles GET requests on a specific quiz
    '''
    quiz = models.Quiz.query.get_or_404(qid)
    return jsonify(quiz.dump_as_dict())



@APP.route('/quizzes/<int:qid>', methods=['DELETE'])
def delete_quizzes(qid):
    '''
    Handles DELETE requests on a specific quiz
    '''
    quiz = models.Quiz.query.get_or_404(qid)
    models.DB.session.delete(quiz)
    models.DB.session.commit()
    response = ('Quiz deleted from database', 200, {"Content-Type": "application/json"})
    #NOTE see previous note about using 204 vs 200
    return make_response(response)



@APP.route('/quizzes/<int:qid>', methods=['PUT'])
def put_quizzes(qid):
    '''
    Handles PUT requests on a specific quiz
    '''
    quiz = models.Quiz.query.get_or_404(qid)

    if not request.json:
        abort(406, "JSON format required for request") # not acceptable

    quiz.title = request.json['title']
    quiz.description = request.json['description']

    # validate that all required information was sent
    if quiz.title is None or quiz.description is None:
        abort(400, "Unable to modify quiz due to missing data") # bad request

    # validate that all required information was sent
    if request.json['questions_ids'] is None:
        abort(400, "Unable to modify quiz due to missing data") # bad request

    quiz.quiz_questions = []
    for qid in request.json['questions_ids']:
        question = models.QuizQuestion.query.get_or_404(qid)
        quiz.quiz_questions.append(question)

    models.DB.session.commit()

    response = ('Quiz updated in database', 200, {"Content-Type": "application/json"})
    #NOTE see previous note about using 204 vs 200
    return make_response(response)
    


@APP.route('/quizzes/<int:qid>/take', methods=['GET'])
def get_quizzes_take(qid):
    '''
    Get the quiz a student is trying to take.
    '''
    quiz = models.Quiz.query.get_or_404(qid)
    return jsonify(quiz.dump_as_dict())



@APP.route('/quizzes/<int:qid>/take', methods=['POST'])
def post_quizzes_take(qid):
    '''
    Post the answers, for the regular quiz mode, or answers along with
    justifications for the asynchronous peer instruction mode.
    '''
    #TODO validate the quiz attempt;
    # ensure that student is authenticated
    # make sure that the student has been assigned this quiz
    # check the due dates for too early / too late
    # check the max duration
    # If answers have already been submitted, accept edits only until due date.
    # make sure quiz mode is peer instruction

    quiz = models.Quiz.query.get_or_404(qid)

    if not request.json:
        abort(406, "JSON format required for request") # not acceptable

    #TODO check if len(responses) == len(justifications) == len(quiz.quiz_questions)
    #TODO check taht that the quiz has not been already attempted

    # validate that all required information was sent
    if request.json['initial_responses'] is None or request.json['justifications'] is None:
        abort(400, "Unable to submit quiz response due to missing data") # bad request

    r = models.QuizAttempt(quiz_id=quiz.id)
    # extract dictionary of question_id : distractor_ID (or none if correct answer)
    r.initial_responses = str(request.json['initial_responses'])
    
    #TODO take into consideration what mode was set by instructor; regular quiz vs. peer instruction quiz
    
    # extract same structure here; distractor_ID : justification
    r.justifications = str(request.json['justifications'])
    
    #TODO set the student_id / timestamps / ... fields

    #TODO do we compute the initial score?
    r.initial_scores = ""

    models.DB.session.add(r)
    models.DB.session.commit()

    response     = ('Quiz attempt recorded in database', 200, {"Content-Type": "application/json"})
    #NOTE see previous note about using 204 vs 200
    return make_response(response)



@APP.route('/quizzes/<int:qid>/review', methods=['GET'])
def get_quizzes_review(qid):
    '''
    Get the specified quiz with peers' answers and justifications
    '''
    quiz = models.Quiz.query.get_or_404(qid)
    #TODO need to also return the answers + justifications of 2 peers
    #TODO what do we do if 2 peers answers are not available?
    # That should not happen if we enforce due dates for review to be past due dates for quiz
    return jsonify(quiz.dump_as_dict())
    
    

@APP.route('/quizzes/<int:qid>/review', methods=['POST'])
def post_quizzes_review(qid):
    '''
    Re-take the specified quiz with peers' answers and justifications
    '''
    #TODO validate the quiz attempt;
    # ensure that student is authenticated
    # make sure that the student has been assigned this quiz
    # check the due dates for too early / too late
    # check the max duration
    # If answers have already been submitted, accept edits only until due date.
    # make sure quiz mode is peer instruction

    #TODO only get answers to all questions; no justifications needed, regardless of quiz mode
    #       Select one of the two students whose answers + justifications were seen as the most useful
    #       Specify which of their justification was the most conductive to learning something.
    #       sounds like we're going to need to make the feedback another model connected 1-to-1
    #       between QuizAttempts
    
    #TODO check if len(responses) == len(quiz.quiz_questions)
    
    # validate that all required information was sent
    if request.json['revised_responses'] is None:
        abort(400, "Unable to submit quiz again due to missing data") # bad request

    quiz = models.Quiz.query.get_or_404(qid)
    
    sid = 1 #FIXME need to use student ID too
    r = models.QuizAttempt.query.get_or_404(quiz_id=quiz.id, student_id=sid)
    #TODO make sure result of the above request is unique

    r.revised_responses = str(request.json['revised_responses'])
        
    #TODO set the student_id / timestamps / ... fields
    
    #TODO do we compute the revised score?
    r.revised_scores = ""

    models.DB.session.add(r)
    models.DB.session.commit()

    response     = ('Quiz answers updated & feeback recorded in database', 0, {"Content-Type": "application/json"})
    #NOTE see previous note about using 204 vs 200
    return make_response(response)


