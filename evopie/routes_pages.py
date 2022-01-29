# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from operator import not_
from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from flask import Blueprint
from flask_login import login_required, current_user
from flask import flash
from sqlalchemy import not_
from sqlalchemy.sql import collate
from flask import Markup
from random import shuffle

import json, random

from . import DB, models

import jinja2


pages = Blueprint('pages', __name__)



@pages.route('/')
def index():
    '''
    Index page for the whole thing; used to test out a rudimentary user interface
    '''
    all_quizzes =  models.Quiz.query.all()
    return render_template('index.html', quizzes=all_quizzes)



@pages.route('/questions-browser')
@login_required
def questions_browser():
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    # working on getting rid of the dump_as_dict and instead using Markup(...).unescape when appropriate
    # all_questions = [q.dump_as_dict() for q in models.Question.query.all()]
    all_questions = models.Question.query.all()
    # TODO this code will have to be refactored into the models; e.g., when adding to DB
    # NOTE this particular one works without doing the following pass on the data, probably bc it's using only the titles in the list
    for q in all_questions:
        q.title = Markup(q.title).unescape()
        q.stem = Markup(q.stem).unescape()
        q.answer = Markup(q.answer).unescape()
    return render_template('questions-browser.html', all_questions = all_questions)
    # version with pagination below
    #page = request.args.get('page',1, type=int)
    #QUESTIONS_PER_PAGE = 10 # FIX ME make this a field in a global config object
    #paginated = models.Question.query.paginate(page, QUESTIONS_PER_PAGE, False)
    #all_questions = [q.dump_as_dict() for q in paginated.items]
    #######return jsonify(all_questions)
    #next_url = url_for('pages.questions_browser', page=paginated.next_num) if paginated.has_next else None
    #prev_url = url_for('pages.questions_browser', page=paginated.prev_num) if paginated.has_prev else None
    #return render_template('questions-browser.html', all_questions = all_questions, next_url=next_url, prev_url=prev_url)



@pages.route('/quizzes-browser')
@login_required
def quizzes_browser():
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    # working on getting rid of the dump_as_dict and instead using Markup(...).unescape when appropriate
    # all_quizzes = [q.dump_as_dict() for q in models.Quiz.query.all()]
    all_quizzes = models.Quiz.query.all()
    return render_template('quizzes-browser.html', all_quizzes = all_quizzes)
    # version with pagination below
    #page = request.args.get('page',1, type=int)
    #QUESTIONS_PER_PAGE = 5 # FIX ME make this a field in a global config object
    #paginated = models.Quiz.query.paginate(page, QUESTIONS_PER_PAGE, False)
    #all_quizzes = [q.dump_as_dict() for q in paginated.items]
    #########return jsonify(all_questions)
    #next_url = url_for('pages.quizzes_browser', page=paginated.next_num) if paginated.has_next else None
    #prev_url = url_for('pages.quizzes_browser', page=paginated.prev_num) if paginated.has_prev else None
    #return render_template('quizzes-browser.html', all_quizzes = all_quizzes, next_url=next_url, prev_url=prev_url)


# NOTE signed=True because flask router won't accept a negative value (or floats for that matter)
# don't need that anymore with the new route after this one
@pages.route('/question-editor/<int(signed=True):question_id>')
@login_required
def question_editor(question_id):
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))

    q = models.Question.query.get_or_404(question_id)
    
    # we replace dump_as_dict with proper Markup(...).unescape of the objects'fields themselves
    #ds = [d.dump_as_dict() for d in q.distractors]
    #q = q.dump_as_dict()
    q.title = Markup(q.title).unescape()
    q.stem = Markup(q.stem).unescape()
    q.answer = Markup(q.answer).unescape()
    for d in q.distractors:
        d.answer = Markup(d.answer).unescape()
    #return render_template('question-editor.html', all_distractors = ds, question = q)
    return render_template('question-editor.html', all_distractors = q.distractors, question = q)
    


@pages.route('/quiz-question-editor/<int:quiz_id>/<int(signed=True):quiz_question_id>')
@login_required
def quiz_question_editor(quiz_id,quiz_question_id):
    
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))

    # we need to create the new question
    if quiz_question_id == -1:
        # create a new blank question
        title = 'Add a title for your new question here.'
        stem = 'Add the question here.'
        answer = 'Add the correct answer to your question here.'
        q = models.Question(title=title, stem=stem, answer=answer)
        models.DB.session.add(q)
        models.DB.session.commit()

        # now link the Question to a new QuizQuestion
        qq = models.QuizQuestion(question=q)
        models.DB.session.add(qq)
        models.DB.session.commit()
    
        # now add the QuizQuestion to the quiz
        my_quiz = models.Quiz.query.get_or_404(quiz_id)
        my_quiz.quiz_questions.append(qq)
        models.DB.session.commit()
    
    else: 
        #q = models.Question.query.get_or_404(question_id)
        qq = models.QuizQuestion.query.get_or_404(quiz_question_id)
        q = models.Question.query.get_or_404(qq.question_id)
        # NOTE we assume that the QuizQuestion already belong to this quiz
        # FIXME we should really ensure that it's the case
        for d in qq.distractors:
            d.answer = Markup(d.answer).unescape()
    # now edit the QuizQuestion
    #return redirect("/question-editor/" + str(q.id), code=302)
    return render_template('quiz-question-editor.html', quiz_id = quiz_id, quiz_question = qq, question = q)



@pages.route('/quiz-question-selector-1/<int:quiz_id>')
@login_required
def quiz_question_selector_1(quiz_id):
    # We selected a quiz by ID. This page will now present all available Question objects
    # and prompt the user to select one to add to the Quiz as a QuizQuestion later
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    questions = models.Question.query.all()
    # unescaping so that the stem and answer are rendered in jinja2 template with | safe
    for q in questions:
        q.stem = Markup(q.stem).unescape()
        q.answer = Markup(q.answer).unescape()
    return render_template('quiz-question-selector-1.html', quiz_id = quiz_id, available_questions = questions)



@pages.route('/quiz-question-selector-2/<int:quiz_id>/<int:question_id>')
@login_required
def quiz_question_selector_2(quiz_id, question_id):
    # Quiz & Question have been selected by ID.
    # We now display all the available distractors for that question and let the user 
    # select a bunch of them.
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    question = models.Question.query.get_or_404(question_id)
    # unescaping so that the stem and answer are rendered in jinja2 template with | safe
    question.stem = Markup(question.stem).unescape()
    question.answer = Markup(question.answer).unescape()
    for d in question.distractors:
        d.answer = Markup(d.answer).unescape()
    return render_template('quiz-question-selector-2.html', quiz_id=quiz_id, question=question)



@pages.route('/quiz-question-selector-3/<int:quiz_id>/<int:question_id>/<selected_distractors>')
@login_required
def quiz_question_selector_3(quiz_id, question_id, selected_distractors):
    # Quiz, Question & some of its distractors have been selected by ID.
    # We create the corresponding QuizQuestion object and add it to the Quiz
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    qz = models.Quiz.query.get_or_404(quiz_id)
    q = models.Question.query.get_or_404(question_id)
    
    #create new QuizQuestion based on the Question
    qq = models.QuizQuestion(question=q)
    
    # distractor IDs are passed as a space-separated string of int values
    # We convert this into a proper list (still of str elements though)
    selected_distractors_list = list(selected_distractors.split(" "))
    
    # we iterate on the above and retrieve each Distractor by its ID
    # before to add it to the QuizQuestion
    for distractor_id_str in selected_distractors_list:
        distractor_id = int(distractor_id_str)
        distractor = models.Distractor.query.get_or_404(distractor_id)
        qq.distractors.append(distractor)
    
    models.DB.session.add(qq)
    models.DB.session.commit()
    # once the QuizQuestion has been committed to the DB, we add it to the Quiz
    qz.quiz_questions.append(qq)
    models.DB.session.commit()

    return render_template("quiz-question-selector-3.html")



@pages.route('/quiz-editor/<int:quiz_id>')
@login_required
def quiz_editor(quiz_id):
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    q = models.Quiz.query.get_or_404(quiz_id)
    # TODO replace dump_as_dict with proper Markup(...).unescape of the objects'fields themselves
    #q = q.dump_as_dict()
    return render_template('quiz-editor.html', quiz = q)
    




@pages.route('/student/<int:qid>', methods=['GET'])
@login_required
def get_student(qid):
    '''
    Links using this route are meant to be shared with students so that they may take the quiz
    and engage in the asynchronous peer instrution aspects. 
    '''
    if not current_user.is_student():
        # response = ({ "message" : "You are not allowed to take this quiz"}, 403, {"Content-Type": "application/json"})
        flash("You are not allowed to take this quiz", "error")
        return redirect(url_for('pages.index'))

    u = models.User.query.get_or_404(current_user.id)
    q = models.Quiz.query.get_or_404(qid)

    # we replace dump_as_dict with proper Markup(...).unescape of the objects'fields themselves
    # see lines commented out a ## for originals
    ##quiz_questions = [question.dump_as_dict() for question in q.quiz_questions]
    quiz_questions = q.quiz_questions

    # TODO FIXME we had to simplify the questions to avoid an escaping problem, fix it when fixing the above
    simplified_quiz_questions = [question.dump_as_simplified_dict() for question in q.quiz_questions]    
    # PBM - the alternatives for questions show unescaped when taking the quiz
    # SOL - need to unescape them before to pass them to the template
    
    ##for qq in quiz_questions:
    ##    for altern in qq["alternatives"]:
    ##        # experimenting, this works: tmp = jinja2.Markup(quiz_questions[0]["alternatives"][0][1]).unescape()
    ##        altern[1] = jinja2.Markup(altern[1]).unescape()
    ##        # nope... altern[1] = jinja2.Markup.escape(altern[1])
    for qq in quiz_questions:
        qq.question.title = Markup(qq.question.title).unescape()
        qq.question.stem = Markup(qq.question.stem).unescape()
        qq.question.answer = Markup(qq.question.title).unescape()
        for d in qq.distractors:
            d.answer = Markup(d.answer).unescape()
        # Preparing the list of alternatives for this question (these are the distractors + answer being displayed in the template)
        # This comes straight from models.py dump_as_dict for QuizQuestion
        tmp1 = [] # list of distractors IDs, -1 for right answer
        tmp2 = [] # list of alternatives, including the right answer
        tmp1.append(-1)
        tmp2.append(Markup(qq.question.answer).unescape())
        for d in qq.distractors:
            tmp1.append(Markup(d.id).unescape()) # FIXME not necessary
            tmp2.append(Markup(d.answer).unescape())
        qq.alternatives = [list(tup) for tup in zip(tmp1,tmp2)]
        shuffle(qq.alternatives)
        # now, each QuizQuestion has an additional field "alternatives"

    # determine which step of the peer instruction the student is in
    a = models.QuizAttempt.query.filter_by(student_id=current_user.id).filter_by(quiz_id=qid).all()
    
    if q.status == "HIDDEN":
        flash("Quiz not accessible at this time", "error")
        return redirect(url_for('pages.index'))

    if a and q.status == "STEP1":
        flash("You already submitted your answers for step 1 of this quiz.", "error")
        flash("Wait for the instructor to open step 2 for everyone.", "error")
        return redirect(url_for('pages.index'))

    if not a and q.status == "STEP2":
        flash("You did not submit your answers for step 1 of this quiz.", "error")
        flash("Because of that, you may not participate in step 2.", "error")
        return redirect(url_for('pages.index'))

    if a and q.status == "STEP2" and a[0].revised_responses != "{}":
        flash("You already submitted your answers for both step 1 and step 2.", "error")
        flash("You are done with this quiz.", "error")
        return redirect(url_for('pages.index'))
        
    # Handle different steps
    if a: # step == 2
        # retrieve the peers' justifications for each question
        quiz_justifications = {}
        for quiz_question in q.quiz_questions:
            question_justifications = {}
            for distractor in quiz_question.distractors:
                # get all justifications for that alternative / question pair
                question_justifications[str(distractor.id)] = models.Justification.query\
                    .filter_by(quiz_question_id=quiz_question.id)\
                    .filter_by(distractor_id=distractor.id)\
                    .filter(not_(models.Justification.justification==""))\
                    .filter(not_(models.Justification.justification=="<br>"))\
                    .filter(not_(models.Justification.justification=="<p><br></p>"))\
                    .filter(not_(models.Justification.justification=="<p></p>"))\
                    .filter(not_(models.Justification.student_id==current_user.id))\
                    .all()
            # also handle the solution -1
            question_justifications["-1"] = models.Justification.query\
                .filter_by(quiz_question_id=quiz_question.id)\
                .filter_by(distractor_id="-1")\
                .filter(not_(models.Justification.justification==""))\
                .filter(not_(models.Justification.justification=="<br>"))\
                .filter(not_(models.Justification.justification=="<p><br></p>"))\
                .filter(not_(models.Justification.justification=="<p></p>"))\
                .filter(not_(models.Justification.student_id==current_user.id))\
                .all()
            
            # NOTE use filter instead of filter_by for != comparisons
            # https://stackoverflow.com/questions/16093475/flask-sqlalchemy-querying-a-column-with-not-equals/16093713

            # record this array of objects as corresponding to this question
            quiz_justifications[str(quiz_question.id)] = question_justifications
            
        # This is where we apply the peer selection policy
        # We now revisit the data we collected and pick one justification in each array of Justification objects
        for key_question in quiz_justifications:
            for key_distractor in quiz_justifications[key_question]:
                #pick multiple of the justification objects at random
                
                #NOTE make sure we check that the len of the array is big enough first
                number_to_select = min(3 , len(quiz_justifications[key_question][key_distractor]))
                #TODO FFS remove the above ugly, hardcoded, magic, number

                selected = []
                for n in range(number_to_select):                     
                    index = random.randint(0,len(quiz_justifications[key_question][key_distractor])-1)
                    neo = quiz_justifications[key_question][key_distractor].pop(index) #[index]
                    selected.append(neo)

                quiz_justifications[key_question][key_distractor] = selected

        initial_responses = [] 

        # FIXME TODO figure out how the JSON got messed up in the first place, then fix it instead of the ugly patch below
        asdict = json.loads(a[0].initial_responses.replace("'",'"'))
        for k in asdict:
            initial_responses.append(asdict[k])

        return render_template('student.html', quiz=q, simplified_questions=simplified_quiz_questions, questions=quiz_questions, student=u, attempt=a[0], initial_responses=initial_responses, justifications=quiz_justifications)

    else: # step == 1

        return render_template('student.html', quiz=q, simplified_questions=simplified_quiz_questions, questions=quiz_questions, student=u)




@pages.route('/grades/<int:qid>', methods=['GET'])
@login_required
def get_grades(qid):
    '''
    This page allows to get all stats on a given quiz.
    '''
    if not current_user.is_instructor():
        flash("Restricted to instructors.", "error")
        return redirect(url_for('pages.index'))
    q = models.Quiz.query.get_or_404(qid)
    # base syntax; returns a list of tupples (blah)
    # grades=DB.session.query(models.QuizAttempt, models.User)\
    #    .filter(models.QuizAttempt.quiz_id == qid)\
    #    .filter(models.QuizAttempt.student_id == models.User.id)\
    #    .all()
    grades=models.QuizAttempt.query.join(models.User)\
        .filter(models.QuizAttempt.quiz_id == qid)\
        .filter(models.QuizAttempt.student_id == models.User.id)\
        .order_by(collate(models.User.last_name, 'NOCASE'))\
        .all()
    return render_template('grades.html', quiz=q, all_grades=grades)