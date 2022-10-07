# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from flask import g, jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from flask import Blueprint
from flask_login import login_required, current_user
from flask import Markup
from flask import flash
from datetime import datetime
from werkzeug.security import generate_password_hash
from evopie.config import QUIZ_ATTEMPT_SOLUTIONS, QUIZ_STEP1, QUIZ_STEP2, QUIZ_ATTEMPT_STEP1, QUIZ_ATTEMPT_STEP2, ROLE_INSTRUCTOR, ROLE_STUDENT
from evopie.evo import get_evo, start_evo, stop_evo, Evaluation

from evopie.utils import groupby, role_required, sanitize, unmime, validate_quiz_attempt_step, verify_deadline

from . import models

mcq = Blueprint('mcq', __name__)

@mcq.route('/questions', methods=['GET'])
@login_required
def get_all_questions():
    '''
    Get, in JSON format, all the questions from the database,
    including, for each, all its distractors.
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to view all questions" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    all_questions = [q.dump_as_dict() for q in models.Question.query.all()]
    return jsonify(all_questions)

@mcq.route('/questions', methods=['POST'])
@login_required
@role_required(ROLE_INSTRUCTOR, redirect_message="You are not allowed to create questions")
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
        #NOTE if the POST from the HTML form refers to an existing question, we forward it to the PUT route.
        # We are able to tell this is the case because the form embeds an hidden field named "qid".
        if 'qid' in request.form:
            return put_question(request.form['qid'])

    # validate that all required information was sent
    if answer is None or stem is None or title is None:
        abort(400, "Unable to create new question due to missing data") # bad request
    
    #NOTE the code below is highly suspicious... why did we keep the jason.dumps lines since both use answer
    # instead of the 2nd line using escaped_answer?
    # Taking a shot at fixing this
    # might be why Paul reported seeing double quotes in the JSON still
    # UPDATE - Not a bug actually...
    # escaped_answer = json.dumps(answer) # escapes "" used in code
    #TODO #3 ok so are we already properly escaping before to commit to the DB?!!
    escaped_answer = Markup.escape(answer) # escapes HTML characters
    escaped_answer = sanitize(escaped_answer)

    # escaped_stem = json.dumps(stem)
    escaped_stem = Markup.escape(stem)
    escaped_stem = sanitize(escaped_stem)

    # escaped_title = json.dumps(title)
    escaped_title = Markup.escape(title)
    escaped_title = sanitize(escaped_title)

    q = models.Question(title=escaped_title, stem=escaped_stem, answer=escaped_answer)
    models.DB.session.add(q)
    models.DB.session.commit()

    if request.json:
        return jsonify({ "message" : "Question & answer added to database", "id": q.id }), 201
    else:
        flash("Question successfully added to database.", "shiny")
        return redirect(request.referrer)    

@mcq.route('/questions/<int:question_id>', methods=['GET'])
@login_required
def get_question(question_id):
    '''
    Get, in JSON format, a specified question from the database.
    We extend here the concept of "Question" by also including ALL its distractors.
    The fact that *all* of the distractors are included is the main difference
    between Question and QuizQuestion.
    While the answer and distractors are shuffled together as alternatives from which
    the student will have to pick, this is not intended to be presented to any
    student since it has ALL the distractors. It is more intended as a debugging
    feature.
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to access individual questions" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    q = models.Question.query.get_or_404(question_id)
    return jsonify(q.dump_as_dict())

@mcq.route('/questions/<int:question_id>', methods=['PUT'])
@login_required
@role_required(ROLE_INSTRUCTOR, redirect_message="You are not allowed to modify questions")
def put_question(question_id):
    '''
    Update a given question.
    This method may be called by post_new_question if we detect a POST request
    coming from an HTML form that really wanted to send us a PUT.
    '''
    # validation - All of the quizzes containing question_id must be HIDDEN to be able to update
    for quiz in models.Quiz.query.all():
        for qq in quiz.quiz_questions:
            if qq.question_id == question_id and quiz.status != "HIDDEN":
                response     = ({ "message" : "Quiz not accessible at this time" }, 403, {"Content-Type": "application/json"})
                return make_response(response)
    
    #NOTE HTML5 forms can not submit a PUT (only POST), so we reject any non-json request
    #NOTE update to the above; we're going to sort out in the POST whether it's a PUT or not
    if not request.json:
        #abort(406, "JSON format required for request") # not acceptable
        title = request.form['title']
        stem = request.form['stem']
        answer = request.form['answer']

    else:
        title = request.json['title']
        stem = request.json['stem']
        answer = request.json['answer']
        
    # validate that all required information was sent
    if answer is None or stem is None or title is None:
        abort(400, "Unable to modify question due to missing data") # bad request
    
    q = models.Question.query.get_or_404(question_id)
    q.title = sanitize(title)
    q.stem = sanitize(stem)
    q.answer = sanitize(answer)

    models.DB.session.commit()
    if request.json:
        response = ({ "message" : "Question updated in database" }, 200, {"Content-Type": "application/json"})
        #NOTE should it be 204? probably but I prefer to return a message so that CURL displays something indicating that the operation succeeded
        return make_response(response)
    else:
        flash("Question successfully updated in database.", "shiny")
        return  redirect(url_for('pages.index'))

@mcq.route('/questions/<int:question_id>', methods=['DELETE'])
@login_required
def delete_question(question_id):
    '''
    Delete given question.
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to delete questions" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    q = models.Question.query.get_or_404(question_id)
    
    # validation - All of the quizzes containing question_id must be HIDDEN to be able to update
    for quiz in models.Quiz.query.all():
        for qq in quiz.quiz_questions:
            if qq.question_id == question_id and quiz.status != "HIDDEN":
                response     = ({ "message" : "Quiz not accessible at this time" }, 403, {"Content-Type": "application/json"})
                return make_response(response)
    
    models.DB.session.delete(q)
    models.DB.session.commit()
    response = ({ "message" : "Question Deleted from database" }, 200, {"Content-Type": "application/json"})
    return make_response(response)

@mcq.route('/questions/<int:question_id>/distractors', methods=['GET'])
@login_required
def get_distractors_for_question(question_id):
    '''
    Get all distractors for the specified question.
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to view individual distractors" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    q = models.Question.query.get_or_404(question_id)
    result = [d.dump_as_dict() for d in q.distractors]
    return jsonify(result)

@mcq.route('/questions/<int:question_id>/distractors', methods=['POST'])
@login_required
@role_required(ROLE_INSTRUCTOR, redirect_message="You are not allowed to create distrators")
def post_new_distractor_for_question(question_id):
    '''
    Add a distractor to the specified question.
    '''
    # validation - All of the quizzes containing question_id must be HIDDEN to be able to add distractor
    # FIXED - not true, the quizzes refer to QuizQuestions which, when added to a Quiz, are characterised
    # by a selection of the available Distractors for their corresponding Question. 
    # As such, if we add a Distractor to a Question later, this does not affect the QuizQuestions already created
    # and thus neither the Quizzes that make use of them.
    if request.json:
        answer = request.json['answer']
        justification = request.json['justification']
    else:
        #FIXME do we want to continue handling both formats?
        answer = request.form['answer']
        justification = request.form['justification']
    
    # detect if did was passed too; if so, then it's an update
    if 'did' in request.form:
        return put_distractor(request.form['did'])


    # validate that all required information was sent
    if answer is None:
        abort(400, "Unable to create new distractor due to missing data") # bad request
    
    q = models.Question.query.get_or_404(question_id)
    
    #NOTE same potential bug here than above, still a feature
    # escaped_answer = json.dumps(answer) # escapes "" used in code
    #TODO #3 same issue here: are we already properly escaping before to commit to DB and, if so, then why do we have to redo it in routes_pages.py when sending the data to the jinja2 templates?!!
    escaped_answer = Markup.escape(answer) # escapes HTML characters
    escaped_answer = sanitize(escaped_answer)

    escaped_justification = Markup.escape(justification)
    escaped_justification = sanitize(escaped_justification)

    new_distractor = models.Distractor(answer=escaped_answer,justification=escaped_justification,question_id=q.id)
    q.distractors.append(new_distractor)
    models.DB.session.commit()
    
    if request.is_json:
        return jsonify({ "message" : "Distractor added to Question in database", "id": new_distractor.id }), 201
    else:
        flash("Distractor successfully added to database.", "shiny")
        return redirect(request.referrer)

@mcq.route('/distractors/<int:distractor_id>', methods=['GET'])
@login_required
def get_distractor(distractor_id):
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to view individual distractors" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    d = models.Distractor.query.get_or_404(distractor_id)
    return jsonify({ "answer": d.answer, "justification": d.justification })

@mcq.route('/distractors/<int:distractor_id>', methods=['PUT','POST'])
@login_required
@role_required(ROLE_INSTRUCTOR, redirect_message="You are not allowed to modify distractors")
def put_distractor(distractor_id):
    # validation - All of the quizzes containing a question that distractor_id is related to must be HIDDEN to be able to update
    for quiz in models.Quiz.query.all():
        for qq in quiz.quiz_questions:
            question = models.Question.query.get(qq.question_id)
            for d in question.distractors:
                if d.id == distractor_id and quiz.status != "HIDDEN":
                    response = ({ "message" : "Quiz not accessible at this time, unable to update distractors." }, 403, {"Content-Type": "application/json"})
                    return make_response(response)
    
    if not request.json:
        #TODO NOW accept form data if it's been sent from the POST handler with an ID
        answer = request.form['answer']
        justification = request.form['justification']
        #abort(406, "JSON format required for request") # not acceptable
    else:
        answer = request.json['answer']    
        justification = request.json['justification']
    
    # validate that all required information was sent
    if answer is None:
        abort(400, "Unable to modify distractor due to missing data") # bad request

    d = models.Distractor.query.get_or_404(distractor_id)
    #d.answer = sanitize(answer)
    #d.justfication = sanitize(justification)
    #BUG here we apply only justification but in one of the above methods we also escape
    d.answer = Markup.escape(answer) # escapes HTML characters
    d.answer = sanitize(d.answer)

    d.justification = Markup.escape(justification)
    d.justification = sanitize(d.justification)

    models.DB.session.commit()

    if request.json:
        response = ({ "message" : "Distractor updated in database" }, 200, {"Content-Type": "application/json"})
        #NOTE see previous note about using 204 vs 200
        return make_response(response)
    else: 
        flash("Distractor successfully modified in database.", "shiny")
        return redirect(request.referrer)

@mcq.route('/distractors/<int:distractor_id>', methods=['DELETE'])
@login_required
def delete_distractor(distractor_id):
    '''
    Delete given distractor.
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to delete distractors" }, 403, {"Content-Type": "application/json"})
        return make_response(response)
    
    d = models.Distractor.query.get_or_404(distractor_id)
    
    # validation - All of the quizzes containing a question that distractor_id is related to must be HIDDEN to be able to update
    for quiz in models.Quiz.query.all():
        for qq in quiz.quiz_questions:
            question = models.Question.query.get(qq.question_id)
            for d in question.distractors:
                if d.id == distractor_id and quiz.status != "HIDDEN":
                    response     = ({ "message" : "Quiz not accessible at this time" }, 403, {"Content-Type": "application/json"})
                    return make_response(response)
    
    models.DB.session.delete(d)
    models.DB.session.commit()
    response = ({ "message" : "Distractor deleted from database" }, 204, {"Content-Type": "application/json"})
    return make_response(response)

@mcq.route('/quizquestions', methods=['GET'])
@login_required
def get_all_quiz_questions():
    '''
    Get, in JSON format, all the QuizQuestions from the database.
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to view all quiz questions" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    all = models.QuizQuestion.query.all()
    result = [q.dump_as_dict() for q in all]
    return jsonify(result)

@mcq.route('/quizquestions', methods=['POST'])
@login_required
def post_new_quiz_question():
    '''
    Add a new QuizQuestion.
    '''
    if not current_user.is_instructor():
        if request.json:
            response     = ({ "message" : "You are not allowed to create quiz questions" }, 403, {"Content-Type": "application/json"})
            return make_response(response)
        else:
            flash("You are not allowed to create quiz questions", "postError")
            return redirect(request.referrer)

    if request.json:
        question_id = request.json['qid']
        if question_id is None or request.json['distractors_ids'] is None:
            abort(400, "Unable to create new quiz question due to missing data") # bad request
        distractors_ids = [did for did in request.json['distractors_ids']]
    else:
        abort(406, "JSON format required for request") # not acceptable
        #TODO apply same modifications tha in post_new_question but also check
        # whether we currently have a form sending that data first
        # NOTE of particular interest is how the form will send those arrays.
        # that was easy in json but I vaguely remember reading some issues
        # with the variable number of fields and regular forms format
    
    
    q = models.Question.query.get_or_404(question_id)
    qq = models.QuizQuestion(question=q)
    distractors = [models.Distractor.query.get_or_404(id) for id in distractors_ids]
    #TODO verify that distractors belong to that question; that led to a funny
    # glitch in the deployement 2021 scripts whereby all distractors were
    # assigned to question #2 by the script but, since they were listed also
    # when creating the QuizQuestion, everything looked like it was working
    # just fine. Beware when your programs look like they are working...
    #TODO verify that distractors are also all different
    
    for d in distractors:
        qq.distractors.append(d)
    
    models.DB.session.add(qq)
    models.DB.session.commit()

    response = ({ "message" : "Quiz Question added to database" }, 201, {"Content-Type": "application/json"})
    return make_response(response)

@mcq.route('/quizquestions/<int:qq_id>', methods=['GET'])
@login_required
def get_quiz_questions(qq_id):
    '''
    Handles GET requests on a specific QuizQuestion
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to access individual quiz questions" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    qq = models.QuizQuestion.query.get_or_404(qq_id)
    return jsonify(qq.dump_as_dict())

@mcq.route('/quizquestions/<int:qq_id>', methods=['DELETE'])
@login_required
def delete_quiz_questions(qq_id):
    '''
    Handles DELETE requests on a specific QuizQuestion
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to delete quiz questions" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    qq = models.QuizQuestion.query.get_or_404(qq_id)

    # validation - All of the quizzes using this qq_id must be HIDDEN to be able to delete
    for quiz in models.Quiz.query.all():
        for qq in quiz.quiz_questions:
            if qq.id == qq_id and quiz.status != "HIDDEN":
                response     = ({ "message" : "Quiz not accessible at this time" }, 403, {"Content-Type": "application/json"})
                return make_response(response)
    
    models.DB.session.delete(qq)
    models.DB.session.commit()
    response = ({ "message" : "Quiz Question Deleted from database" }, 200, {"Content-Type": "application/json"})
    #NOTE see previous note about using 204 vs 200
    #NOTE the above is a bloody tuple, not 3 separate parameters to make_response
    return make_response(response)

@mcq.route('/quizquestions/<int:qq_id>', methods=['PUT'])
@login_required
def put_quiz_questions(qq_id):
    '''
    Handles PUT requests on a specific QuizQuestion
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to modify quiz questions" }, 403, {"Content-Type": "application/json"})
        return make_response(response)
    
    qq = models.QuizQuestion.query.get_or_404(qq_id)

    # validation - All of the quizzes using this qq_id must be HIDDEN to be able to update
    for quiz in models.Quiz.query.all():
        for qq in quiz.quiz_questions:
            if qq.id == qq_id and quiz.status != "HIDDEN":
                response     = ({ "message" : "Quiz not accessible at this time" }, 403, {"Content-Type": "application/json"})
                return make_response(response)
        
    if not request.json:
        abort(406, "JSON format required for request") # not acceptable

    # validate that all required information was sent
    if request.json['qid'] is None or request.json['distractors_ids'] is None:
        abort(400, "Unable to modify quiz question due to missing data") # bad request

    question_id = request.json['qid']
    distractors_ids = [did for did in request.json['distractors_ids']]

    qq.question = models.Question.query.get_or_404(question_id)
    distractors = [models.Distractor.query.get_or_404(id) for id in distractors_ids]

    qq.distractors = distractors
    models.DB.session.commit()

    response = ({ "message" : "Quiz Question updated in database" }, 201, {"Content-Type": "application/json"})
    return make_response(response)

@mcq.route('/quizzes', methods=['POST'])
@login_required
@role_required(ROLE_INSTRUCTOR, redirect_message="You are not allowed to create quizzes")
def post_new_quiz():
    '''
    Create a new quiz
    '''
    title = request.json['title']
    description = request.json['description']
    deadline0 = datetime.strptime(request.json['deadline0'], '%Y-%m-%dT%H:%M')
    deadline1 = datetime.strptime(request.json['deadline1'], '%Y-%m-%dT%H:%M')
    deadline2 = datetime.strptime(request.json['deadline2'], '%Y-%m-%dT%H:%M')
    deadline3 = datetime.strptime(request.json['deadline3'], '%Y-%m-%dT%H:%M')
    deadline4 = datetime.strptime(request.json['deadline4'], '%Y-%m-%dT%H:%M')

    if deadline0 > deadline1 or deadline1 > deadline2 or deadline2 > deadline3 or deadline3 > deadline4:
        flash("Invalid deadline sequence", "error")
        abort(400, "Unable to create quiz due to invalid deadlines")

    # validate that all required information was sent
    if title is None or description is None:
        abort(400, "Unable to create new quiz due to missing data") # bad request

    #if request.json['questions_ids'] is None:
    #    abort(400, "Unable to create new quiz due to missing data") # bad request
    
    bleached_title = sanitize(title)
    bleached_description = sanitize(description)

    q = models.Quiz(title=bleached_title, description=bleached_description, deadline0=deadline0, deadline1=deadline1, deadline2=deadline2, deadline3=deadline3, deadline4=deadline4)
    
    # Adding the questions, based on the questions_id that were submitted
    if 'questions_ids' in request.json:
        for qid in request.json['questions_ids']:
            question = models.QuizQuestion.query.get_or_404(qid)
            q.quiz_questions.append(question)
    
    models.DB.session.add(q)
    models.DB.session.commit()

    return jsonify({ "message" : "Quiz added to database", "id": q.id }), 201

@mcq.route('/quizzes', methods=['GET'])
@login_required
def get_all_quizzes():
    '''
    Get us all quizzes, for debugging purposes
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to view all quizzes" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    quizzes = models.Quiz.query.all()
    return jsonify([q.dump_as_dict()for q in quizzes])

@mcq.route('/quizzes/<int:qid>', methods=['GET'])
@login_required
def get_quizzes(qid):
    '''
    Handles GET requests on a specific quiz
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to download individual quizzes" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    quiz = models.Quiz.query.get_or_404(qid)
    return jsonify(quiz.dump_as_dict())

@mcq.route('/quizzes/<int:qid>', methods=['DELETE'])
@login_required
def delete_quizzes(qid):
    '''
    Handles DELETE requests on a specific quiz
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to delete quizzes" }, 403, {"Content-Type": "application/json"})
        return make_response(response)
    quiz = models.Quiz.query.get_or_404(qid)

    # validation - quiz must be HIDDEN to be able to delete w/o affecting students who are taking it
    if quiz.status != "HIDDEN":
        response     = ({ "message" : "Quiz not accessible at this time" }, 403, {"Content-Type": "application/json"})
        return make_response(response)
    

    models.DB.session.delete(quiz)
    models.DB.session.commit()
    response = ({ "message" : "Quiz deleted from database" }, 200, {"Content-Type": "application/json"})
    #NOTE see previous note about using 204 vs 200
    return make_response(response)

@mcq.route('/quizzes/<int:qid>', methods=['PUT'])
@login_required
def put_quizzes(qid):
    '''
    Handles PUT requests on a specific quiz
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to modify quizzes" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    quiz = models.Quiz.query.get_or_404(qid)

    # validation - quiz must be HIDDEN to be able to modify w/o affecting students who are taking it
    if quiz.status != "HIDDEN":
        response     = ({ "message" : "Quiz not accessible at this time" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    if not request.json:
        abort(406, "JSON format required for request") # not acceptable

    # validate that all required information was sent
    if quiz.title is None or quiz.description is None:
        #removing this one since we can POST just the title + description
        #  or request.json['questions_ids'] is None:
        abort(400, "Unable to modify quiz due to missing data") # bad request

    quiz.title = sanitize(request.json['title'])
    quiz.description = sanitize(request.json['description'])

    # if no questions_ids are passed, we just update the above title and description
    # please note that we may receive an empty list of questions_ids thus meaning we removed all questions
    # from a given quiz
    if 'questions_ids' in request.json.keys():
        quiz.quiz_questions = []
        for qid in request.json['questions_ids']:
            question = models.QuizQuestion.query.get_or_404(qid)
            quiz.quiz_questions.append(question)

    models.DB.session.commit()

    response = ({ "message" : "Quiz updated in database" }, 200, {"Content-Type": "application/json"})
    #NOTE see previous note about using 204 vs 200
    return make_response(response)
    
@mcq.route('/quizzes/<int:qid>/status', methods=['GET'])
@login_required
@role_required(role=ROLE_INSTRUCTOR)
def get_quizzes_status(qid):
    '''
    Returns the status of a given quiz
    '''
    quiz = models.Quiz.query.get_or_404(qid)
    return jsonify({"status": quiz.status})

@mcq.route('/quizzes/<int:qid>/status', methods=['POST'])
@login_required
@role_required(role=ROLE_INSTRUCTOR)
def post_quizzes_status(qid):
    '''
    Modifies the status of given quiz
    '''

    quiz = models.Quiz.query.get_or_404(qid)

    if not request.is_json:
        abort(406, "JSON format required for request") # not acceptable
    new_status = sanitize(request.json['status'])
    # FIXED how about check that the status is actually valid, eh? :)'
    # done in set_status below
    if(quiz.set_status(new_status)):
        response     = ({ "message" : "OK" }, 200, {"Content-Type": "application/json"})        
        models.DB.session.commit()
        if quiz.status == "STEP1": 
            #starting evo process for quiz 
            # start_default_p_phc(quiz)
            start_evo(quiz.id)
        else: 
            #ending evo process for quiz 
            stop_evo(quiz.id)
    else:
        response     = ({ "message" : "Unable to switch to new status" }, 400, {"Content-Type": "application/json"})
    return make_response(response)

@mcq.route('/quizzes/<int:qid>/take', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_STUDENT, redirect_route='pages.index', redirect_message="You are not allowed to take quizzes", category="postError")
@verify_deadline(redirect_route='pages.index')
def all_quizzes_take(qid):

    quiz = models.Quiz.query.get_or_404(qid)
    
    sid = current_user.id
    
    # TODO implement logic for deadlines
    # IF date <= DL1 THEN step #1 ELSE IF DL1 < date <= DL2 && previous attempt exists THEN step #2

    attempt = models.QuizAttempt.query.filter_by(quiz_id=qid).filter_by(student_id=sid).first()
    # FIXME we are taking the first... would be better to ensure uniqueness


    # NOTE need to code for step1 and step2

    # if attempt.status == QUIZ_ATTEMPT_STEP1:
    #     if date > quiz.deadline0 and date <= quiz.deadline1 and quiz.status == QUIZ_STEP1:
    
    step1 = False
    step2 = False
    
    # NOTE old way to determine our step
    ## Is the student POSTing initial answer (step 1) or revised answers (step 2)
    ##if attempt is None:
    ##    step1 = True
    ##else:
    ##    step2 = True
    
    # new way to do so
    if quiz.status == "HIDDEN":
        response     = ({ "message" : "Quiz not accessible at this time" }, 403, {"Content-Type": "application/json"})
        return make_response(response)
    
    step1 = (quiz.status == "STEP1" and ((attempt is None) or (attempt.status == QUIZ_ATTEMPT_STEP1)))
    step2 = (quiz.status == "STEP2" and ((attempt is not None) and (attempt.status == QUIZ_ATTEMPT_STEP2)))

    # sanity check
    if step1 == step2:
        # we have an issue, either the student should be taking simultaneously the two steps of the
        # quiz, which would be a BUG or they should take none, which most likely means the quiz is not yet available
        response     = ({ "message" : "Quiz not accessible at this time" }, 403, {"Content-Type": "application/json"})
        #NOTE 403 is better here than 401 (unauthorized) here since there is no issue w/ auth
        return make_response(response)

    if request.method == 'GET':

        if step1:
            return jsonify(quiz.dump_as_dict())
        else: #step2
            #TODO need to also return the answers + justifications of 2 peers
            #TODO what do we do if n peers answers are not available? with n+1 being # options for MCQ
            # That should not happen if we enforce due dates for review to be past due dates for quiz
            return jsonify(quiz.dump_as_dict())

    else: #request.method == 'POST'
        # NOTE sanity check
        # if len(responses) == len(justifications) == len(quiz.quiz_questions)

        if not request.json:
            abort(406, "JSON format required for request") # not acceptable
        
        if step1:
            # validate that all required information was sent
            # BUG if the keys are missing we crash
            if 'initial_responses' not in request.json or 'justifications' not in request.json:
                abort(400, "Unable to submit quiz response due to missing data") # bad request

            # Being in step 1 means that the quiz has not been already attempted
            # i.e., QuizAttempt object for this quiz & student combination does not already exist
            # if attempt is not None: # NOTE should never happen
            #     abort(400, "Unable to submit quiz, already existing attempt previously submitted") # bad request

            # so we make a brand new one!
            if attempt is None:
                attempt = models.QuizAttempt(quiz_id=quiz.id, student_id=sid, alternatives=[]) #unknown alternatives set 
            attempt.status = QUIZ_ATTEMPT_STEP2
            
            # extract from request the dictionary of question_id : distractor_ID (or None if correct answer)
            
            # we save a string version of this data in the proper field
            attempt.initial_responses = request.json['initial_responses']###
            # we compute a dictionary of question_id : score in which score is 0 or 1
            #   1 means the student selected the solution (None shows in the responses)
            #   0 means the student selected one of the distractors (its ID shows in the responses)
            attempt.initial_scores = {}
            # we also save the total score as we go
            attempt.initial_total_score = 0
            for qid, answer in attempt.initial_responses.items():
                if answer == 0:
                    response     = ({ "message" : "You must select an answer for each question" }, 400, {"Content-Type": "application/json"})
                    return make_response(response)
                if answer < 0:
                    result = 1
                else:
                    result = 0
                attempt.initial_scores[qid] = result
                attempt.initial_total_score += result

            # extract same structure here; question_id : justification string
            justifications_dict = request.json['justifications']
            attempt.justifications = str(justifications_dict)
            
            # check that every alternative that was not selected has a justification
            for key_quest in justifications_dict:
                quest = justifications_dict[key_quest]
                for key_just in quest:
                    if quest[key_just] == "" and key_just != attempt.initial_responses[key_quest]:
                        response     = ({ "message" : "You must provide a justification for each option" }, 400, {"Content-Type": "application/json"})
                        return make_response(response)

            # Record in DB the justification with quizquestion id + distractor id + student ID--> justifications
            for key_quest in justifications_dict:
                quest = justifications_dict[key_quest]
                for key_just in quest:
                    just = models.Justification(quiz_question_id=key_quest, distractor_id=key_just, student_id=sid, justification=sanitize(quest[key_just]), seen=0)
                    models.DB.session.add(just)
            models.DB.session.add(attempt)
            models.DB.session.commit()

            evo = get_evo(quiz.id)
            if evo is not None: 
                answers = { int(q_id): answer for q_id, answer in attempt.initial_responses.items() }
                evo.set_evaluation(Evaluation(evaluator_id=sid, result=answers))

            response     = ({ "message" : "Quiz attempt recorded in database" }, 200, {"Content-Type": "application/json"})
            # NOTE see previous note about using 204 vs 200
            return make_response(response)


        else: #step2
            # validate that all required information was sent
            if request.json['revised_responses'] is None:
                abort(400, "Unable to submit quiz again due to missing data") # bad request
            
            if attempt is None:
                abort(404)

            attempt.status = QUIZ_ATTEMPT_SOLUTIONS
    
            #TODO only get answers to all questions; no justifications needed, regardless of quiz mode
            #       Select one of the two students whose answers + justifications were seen as the most useful
            #       Specify which of their justification was the most conductive to learning something.
            #       sounds like we're going to need to make the feedback another model connected 1-to-1
            #       between QuizAttempts
            
            # we update the existing attempt with step 2 information
            revised_responses_dict = request.json['revised_responses']
            revised_scores_dict = {}
            attempt.revised_responses = str(revised_responses_dict)
            # we also save the total score as we go
            attempt.revised_total_score = 0
            for key in revised_responses_dict:
                if int(revised_responses_dict[key] == 0):
                    response     = ({ "message" : "You must select an answer for each question" }, 400, {"Content-Type": "application/json"})
                    return make_response(response)
                if int(revised_responses_dict[key]) < 0:
                    result = 1
                else:
                    result = 0
                revised_scores_dict[key] = result
                attempt.revised_total_score += result
            attempt.revised_scores = str(revised_scores_dict)
            
            models.DB.session.commit()

            response     = ({ "message" : "Quiz answers updated & feeback recorded in database" }, 200, {"Content-Type": "application/json"})
            #NOTE see previous note about using 204 vs 200
            return make_response(response)

@mcq.route('/quizzes/<int:qid>/responses', methods=['GET'])
@login_required
def get_quizzes_responses(qid):
    '''
    Returns all the data on all the attempts made so far on that quiz by students.
    '''
    if not current_user.is_instructor():
        response     = ({ "message" : "You are not allowed to view quizzes responses" }, 403, {"Content-Type": "application/json"})
        return make_response(response)

    attempts = models.QuizAttempt.query.filter_by(quiz_id=qid).all()
    return jsonify([a.dump_as_dict() for a in attempts])

@mcq.route('/grades/<int:qid>/settings', methods=['POST'])
@login_required
@role_required(role=ROLE_INSTRUCTOR)
def post_grading_settings(qid):
    q = models.Quiz.query.get_or_404(qid)        
    if request.is_json:
        if 'initial_score' in request.json:
            q.initial_score_weight = int(request.json['initial_score']) / 100 
        if 'revised_score' in request.json:
            q.revised_score_weight = int(request.json['revised_score']) / 100
        if 'justification_grade' in request.json:
            q.justification_grade_weight = int(request.json['justification_grade']) / 100
        if 'participation_grade' in request.json:
            q.participation_grade_weight = int(request.json['participation_grade']) / 100 
        if 'num_justifications_shown' in request.json:
            q.num_justifications_shown = int(request.json['num_justifications_shown'])  
        if 'first_quartile_grade' in request.json:
            q.first_quartile_grade = int(request.json['first_quartile_grade'])
        if 'second_quartile_grade' in request.json:
            q.second_quartile_grade = int(request.json['second_quartile_grade'])
        if 'third_quartile_grade' in request.json:
            q.third_quartile_grade = int(request.json['third_quartile_grade'])
        if 'fourth_quartile_grade' in request.json:
            q.fourth_quartile_grade = int(request.json['fourth_quartile_grade']) 
        if 'limiting_factor' in request.json:
            q.limiting_factor = int(request.json['limiting_factor']) / 100
            attempts = models.QuizAttempt.query.filter_by(quiz_id = qid).all()
            for a in attempts:
                a.participation_grade_threshold = round(a.max_likes * q.limiting_factor)
        models.DB.session.commit()
    return jsonify(q.dump_as_dict())

@mcq.route('/quizzes/<qa:q>/justifications', methods=['GET'])
@login_required
def get_quiz_justifications(q):
    _, attempt = q
    dids = [d for q in attempt.alternatives for d in q['alternatives'] ]
    js = models.Justification.query.where(models.Justification.distractor_id.in_(dids), student_id = current_user.id).all()
    return {"justifications":[j.dump_as_dict() for j in js]}

@mcq.route('/quizzes/<qa:q>/answers', methods=['PUT'])
@login_required
@validate_quiz_attempt_step(quiz_attempt_param = "q")
@unmime(type_converters={"*":lambda x: int(x)})
def answer_questions(q, body):
    _, attempt = q

    for qid, answer in body.items(): # body should be map of questionId: id of option selected
        if qid in attempt.alternatives_map and answer >= 0 and answer < len(attempt.alternatives_map[qid]):
            attempt.step_responses[qid] = attempt.alternatives_map[qid][answer]
        # if qid in attempt.alternatives_map and int(answer) in attempt.alternatives_map[qid]:
        #     attempt.step_responses[qid] = int(answer)
    
    models.DB.session.commit()
    return {"message": "Quiz answers were saved"}

@mcq.route('/quizzes/<qa:q>/justifications', methods=['PUT', 'DELETE'])
@login_required
@validate_quiz_attempt_step(quiz_attempt_param = "q")
@unmime()
def justify_alternative_selection(q, body):
    ''' Creates or saves justification into database
        NOTE: alterantive_id is not distractor id, but id as it appearch on UI - for security reasons
        TODO: security checks that student has access to specified quiz - multiinstractor support should provide this
        NOTE: body should be in form {'<qid>': {'<altId>':<text>}}
    '''        
    _, attempt = q

    new_justifications = {(int(qid), distractor_id):justification
        for qid, alt_js in body.items()
        for alternatives in [ attempt.alternatives_map[qid] ]
        for alt_id, justification in alt_js.items()
        for aid in [int(alt_id)]
        if aid >= 0 and aid < len(alternatives)        
        for distractor_id in [ alternatives[aid] ] }

    # new_justifications = {(int(qid), aid):justification
    #     for qid, alt_js in body.items()
    #     for alternatives in [ attempt.alternatives_map[qid] ]
    #     for alt_id, justification in alt_js.items()
    #     for aid in [int(alt_id)]
    #     if aid in alternatives }

    if len(new_justifications) == 0: 
        return {"message": "Justifications were saved" }

    question_ids, distractor_ids = zip(*new_justifications.keys())

    justifications_plain = models.Justification.query.where(models.Justification.quiz_question_id.in_(question_ids), models.Justification.distractor_id.in_(distractor_ids), models.Justification.student_id == current_user.id).all()    
    justifications = {(j.quiz_question_id, j.distractor_id):j for j in justifications_plain if (j.quiz_question_id, j.distractor_id) in new_justifications }
    if request.method == 'DELETE':
        for j in justifications.values():
            models.DB.session.delete(j)    
        models.DB.session.commit()
        return {"message": "Justifications were deleted"} #TODO: add ids of deleted entities or entities themselves
    # resp_added_just_ids = {}
    for (qid, did), new_j in new_justifications.items():
        if (qid, did) in justifications:
            if new_j == '':
                models.DB.session.delete(justifications[(qid, did)])    
            else:
                justifications[(qid, did)].justification = new_j
        elif new_j != '': 
            justification = models.Justification(quiz_question_id = qid, distractor_id = did, student_id = current_user.id, justification = new_j)
            # resp_added_just_ids.setdefault(str(justification.quiz_question_id), {})[str(justification.distractor_id)] = justification
            models.DB.session.add(justification)
    models.DB.session.commit() #after this point all ids for added_justifications were assigned 
    # resp_added_just_ids = {qid:{did:j.id for did, j in qjs.items()} for qid, qjs in resp_added_just_ids.items()}
    return {"message": "Justifications were saved" } #TODO: return ids of created entities

@mcq.route('/quizzes/<qa:q>/justifications/like', methods=['PUT'])
@login_required
@verify_deadline(quiz_attempt_param = "q", redirect_route='pages.index')
@validate_quiz_attempt_step(quiz_attempt_param = "q", required_step=QUIZ_ATTEMPT_STEP2)
@unmime(type_converters={"*": lambda x: x == 1}) #1 means like, 0 - unlike
def like_justifications(q, body):
    _, attempt = q 
    
    if hasattr(g, "ignore_selected_justifications") and g.ignore_selected_justifications: #disablces validation of ids 
        present_likes = models.Likes4Justifications.query.where(models.Likes4Justifications.student_id == current_user.id).all()
        present_likes_map = {str(l.justification_id):l for l in present_likes}   
        valid_jid = lambda jid: True     
    else: 
        jids = set(j.id for j in attempt.selected_justifications)
        present_likes = models.Likes4Justifications.query.where(models.Likes4Justifications.student_id == current_user.id,
            models.Likes4Justifications.justification_id.in_(jids)).all()
        present_likes_map = {str(l.justification_id):l for l in present_likes}
        valid_jid = lambda jid: int(jid) in jids

    for jid, is_liked in body.items():
        if is_liked and jid not in present_likes_map and valid_jid(jid):
            models.DB.session.add(models.Likes4Justifications(student_id = current_user.id, justification_id = int(jid)))
        elif not is_liked and jid in present_likes_map:
            models.DB.session.delete(present_likes_map[jid])
    
    models.DB.session.commit()

    return { "message" : "ok with no contents to send back" }

@mcq.route('/users/<int:uid>/role', methods=['POST'])
@login_required
def post_users_role(uid):
    '''
    Modifies the role of given user
    '''
    if not current_user.is_admin():
        if request.json:
            response     = ({ "message" : "You are not allowed to change user roles" }, 403, {"Content-Type": "application/json"})
            return make_response(response)
        else:
            flash("You are not allowed to change user roles", "postError")

    user = models.User.query.get_or_404(uid)

    if not request.json:
        abort(406, "JSON format required for request") # not acceptable
    new_role = sanitize(request.json['role'])
    if(user.set_role(new_role)):
        response     = ({ "message" : "OK" }, 200, {"Content-Type": "application/json"})
        models.DB.session.commit()
    else:
        response     = ({ "message" : "Unable to switch to new role" }, 400, {"Content-Type": "application/json"})
    return make_response(response)

@mcq.route('/users/<int:uid>/password', methods=['POST'])
def post_user_password(uid):
    if request.json:
        password = request.json['password']
    else:
        password = request.form.get('password')
        
    password = generate_password_hash(password, method='sha256')
    user = models.User.query.get_or_404(uid)
    user.password = password
    models.DB.session.commit()

    return redirect(url_for('pages.users_browser'))

