# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from datetime import datetime
import io
from math import exp
from mimetypes import init
from operator import not_
import random
from tracemalloc import start
from flask import g, jsonify, abort, request, Response, render_template, redirect, url_for, make_response, send_file
from flask import Blueprint
from flask_login import login_required, current_user
from flask import flash
from pandas import DataFrame
from sqlalchemy import not_
from sqlalchemy.sql import collate
from flask import Markup
from evopie.quiz_model import get_quiz_builder
from evopie.routes_mcq import answer_questions, justify_alternative_selection
from werkzeug.security import check_password_hash

from evopie.utils import find_median, unescape, groupby
from evopie.decorators import role_required, retry_concurrent_update

from .config import QUIZ_ATTEMPT_SOLUTIONS, QUIZ_ATTEMPT_STEP1, QUIZ_ATTEMPT_STEP2, QUIZ_ATTEMPT_STEP3, QUIZ_HIDDEN, QUIZ_SOLUTIONS, QUIZ_STEP1, QUIZ_STEP2, QUIZ_STEP3, ROLE_INSTRUCTOR, ROLE_STUDENT, get_attempt_next_step, get_k_tournament_size, get_least_seen_slots_num
from evopie.decorators import unmime, validate_quiz_attempt_step, verify_deadline, verify_instructor_relationship, change_quiz_status

from dataclasses import dataclass

from . import DB, models

import jinja2

#used for justification histogram rendering
import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42


pages = Blueprint('pages', __name__)

@pages.route('/')
def index():
    ''' Index page for the whole thing; used to test out a rudimentary user interface '''
    courses = []
    attempts = {}
    if current_user.is_authenticated and current_user.is_student():
        courses = current_user.courses
        for course in courses:
            for quiz in course.quizzes:
                attempts[quiz.id] = models.QuizAttempt.query.filter_by(quiz_id=quiz.id, student_id=current_user.get_id(), course_id=course.id).first()
                if quiz.deadline_driven == "True":
                    change_quiz_status(quiz)

    return render_template('index.html', courses=courses, attempts=attempts)

@pages.route('/questions-browser')
@login_required
def questions_browser():
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    # working on getting rid of the dump_as_dict and instead using Markup(...).unescape when appropriate
    # all_questions = [q.dump_as_dict() for q in models.Question.query.all()]
    all_questions = models.Question.query.filter_by(author_id=current_user.get_id()).all()
    # NOTE TODO #3 this particular one works without doing the following pass on the data, probably bc it's using only the titles in the list
    for q in all_questions:
        q.title = unescape(q.title)
        q.stem = unescape(q.stem)
        q.answer = unescape(q.answer)
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
    # TODO #3 working on getting rid of the dump_as_dict and instead using Markup(...).unescape when appropriate
    # all_quizzes = [q.dump_as_dict() for q in models.Quiz.query.all()]
    all_quizzes = models.Quiz.query.filter_by(author_id=current_user.get_id()).all()
    new_quizzes = []
    for q in all_quizzes:
        courses = [ c.dump_as_dict() for c in q.courses ]
        if len(courses) == 0:
            new_quizzes.append(q)
    courses = models.Course.query.filter_by(instructor_id=current_user.get_id()).all()

    return render_template('quizzes-browser.html', new_quizzes = new_quizzes, courses = courses)
    # version with pagination below
    #page = request.args.get('page',1, type=int)
    #QUESTIONS_PER_PAGE = 5 # FIX ME make this a field in a global config object
    #paginated = models.Quiz.query.paginate(page, QUESTIONS_PER_PAGE, False)
    #all_quizzes = [q.dump_as_dict() for q in paginated.items]
    #########return jsonify(all_questions)
    #next_url = url_for('pages.quizzes_browser', page=paginated.next_num) if paginated.has_next else None
    #prev_url = url_for('pages.quizzes_browser', page=paginated.prev_num) if paginated.has_prev else None
    #return render_template('quizzes-browser.html', all_quizzes = all_quizzes, next_url=next_url, prev_url=prev_url)

@pages.route('/courses-browser')
@login_required
@role_required(ROLE_INSTRUCTOR)
def courses_browser():
    all_courses = models.Course.query.filter_by(instructor_id=current_user.get_id()).all()
    return render_template('courses-browser.html', all_courses = all_courses)


# NOTE signed=True because flask router won't accept a negative value (or floats for that matter)
# don't need that anymore with the new route after this one
@pages.route('/question-editor/<int(signed=True):question_id>')
@login_required
def question_editor(question_id):
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))

    q = models.Question.query.get_or_404(question_id)
    
    # TODO #3 we replace dump_as_dict with proper Markup(...).unescape of the objects'fields themselves
    #ds = [d.dump_as_dict() for d in q.distractors]
    #q = q.dump_as_dict()
    q.title = unescape(q.title)
    q.stem = unescape(q.stem)
    q.answer = unescape(q.answer)
    for d in q.distractors:
        d.answer = unescape(d.answer)
        d.justification = unescape(d.justification)
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
            d.answer = unescape(d.answer)
            d.justification = unescape(d.justification)
            
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
    for q in questions:
        q.stem = unescape(q.stem)
        q.answer = unescape(q.answer)
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
    question.stem = unescape(question.stem)
    question.answer = unescape(question.answer)
    for d in question.distractors:
        d.answer = unescape(d.answer)
        d.justification = unescape(d.justification)
    
    return render_template('quiz-question-selector-2.html', quiz_id=quiz_id, question=question)

@pages.route('/quiz-question-selector-2/<int:quiz_id>/<int:question_id>', methods=['POST'])
@login_required
def add_quiz_question_to_quiz(quiz_id, question_id):
    # Quiz & Question have been selected by ID.
    # We now display all the available distractors for that question and let the user 
    # select a bunch of them.
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))

    qz = models.Quiz.query.get_or_404(quiz_id)
    q = models.Question.query.get_or_404(question_id)
    
    #create new QuizQuestion based on the Question
    qq = models.QuizQuestion(question=q) 

    if request.is_json:
        selected_distractors_list = request.json.get('selected_distractors')
    else:
        selected_distractors_list = request.form.get('selected_distractors')

    if len(selected_distractors_list) == 0:
        return { "message" : "Select atleast one distractor to continue!", "redirect": url_for("pages.quizzes_browser"), "status": "danger" }, 400

    for distractor_id_str in selected_distractors_list:
        distractor_id = int(distractor_id_str)
        distractor = models.Distractor.query.get_or_404(distractor_id)
        qq.distractors.append(distractor)
    
    models.DB.session.add(qq)
    models.DB.session.commit()
    # once the QuizQuestion has been committed to the DB, we add it to the Quiz
    qz.quiz_questions.append(qq)
    models.DB.session.commit()

    return { "message" : "Question added to Quiz! Redirecting to Quiz Browser...", "redirect": url_for("pages.quizzes_browser"), "status": "success" }, 200

@pages.route('/course-editor/<int:course_id>')
@login_required
@role_required(ROLE_INSTRUCTOR)
def course_editor(course_id):
    course = models.Course.query.get_or_404(course_id)
    quizzes = models.Quiz.query.filter_by(author_id = current_user.id).all()

    available_quizzes = []
    for q in quizzes:
        if q not in course.quizzes:
            available_quizzes.append(q)
            
    return render_template('course-editor.html', course=course, quizzes=available_quizzes)

@pages.route('/course-editor/<int:course_id>', methods=['POST'])
@login_required
@role_required(ROLE_INSTRUCTOR)
def course_editor_post(course_id):
    course = models.Course.query.get_or_404(course_id)
    if request.is_json:
        selected_quizzes_list = request.json.get('selected_quizzes')
    else:
        selected_quizzes_list = request.form.get('selected_quizzes')

    if len(selected_quizzes_list) == 0:
        return { "message" : "Select atleast one quiz to continue!", "redirect": url_for("pages.courses_browser"), "status": "danger" }, 400

    for quiz_id_str in selected_quizzes_list:
        quiz_id = int(quiz_id_str)
        quiz = models.Quiz.query.get_or_404(quiz_id)
        quiz.courses.append(course)
    
    models.DB.session.commit()
    return { "message" : "Added quizzes to the course!", "redirect": url_for("pages.courses_browser"), "status": "success" }, 200

@pages.route('/quiz-editor/<int:quiz_id>')
@login_required
def quiz_editor(quiz_id):
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    q = models.Quiz.query.get_or_404(quiz_id)
    courses = models.Course.query.filter_by(instructor_id=current_user.get_id()).all()
    # TODO #3 we replace dump_as_dict with proper Markup(...).unescape of the objects'fields themselves
    #q = q.dump_as_dict()
    for qq in q.quiz_questions:
        qq.question.title = unescape(qq.question.title)
        qq.question.stem = unescape(qq.question.stem)
        qq.question.answer = unescape(qq.question.answer)
        # NOTE we do not have to worry about unescaping the distractors because the quiz-editor 
        # does not render them. However, if we had to do so, remember that we need to add to 
        # each QuizQuestion a field named alternatives that has the answer + distractors unescaped.
    if q.status != "HIDDEN":
        flash("Quiz not editable at this time", "error")
        return redirect(request.referrer)
    numJustificationsOptions = [num for num in range(1, 11)]
    limitingFactorOptions = [num for num in range(1, 100)]
    initialScoreFactorOptions = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    revisedScoreFactorOptions = initialScoreFactorOptions
    justificationsGradeOptions = initialScoreFactorOptions
    participationGradeOptions = initialScoreFactorOptions
    quartileOptions = numJustificationsOptions
    return render_template('quiz-editor.html', quiz = q.dump_as_dict(), limitingFactorOptions = limitingFactorOptions, initialScoreFactorOptions = initialScoreFactorOptions, revisedScoreFactorOptions = revisedScoreFactorOptions, justificationsGradeOptions = justificationsGradeOptions, participationGradeOptions = participationGradeOptions, numJustificationsOptions = numJustificationsOptions, quartileOptions = quartileOptions, courses = courses)

@pages.route('/quiz-configuration/<quiz:q>')
@login_required
@role_required(ROLE_INSTRUCTOR, redirect_route='pages.index', redirect_message="Restricted to contributors")
def quiz_configuration(q):
    return render_template('quiz-configuration.html', quiz = q.dump_as_dict())

@pages.route('/quiz-configuration/<quiz:q>', methods=['POST'])
@login_required
@role_required(ROLE_INSTRUCTOR, redirect_message="You are not allowed to modify quiz configuration")
@unmime(delim='-')
def update_quiz_configuration(q, body):
    ''' Separate quiz configuration update endpoint '''
    deadline0 = datetime.strptime(body['deadline0'], '%Y-%m-%dT%H:%M')
    deadline1 = datetime.strptime(body['deadline1'], '%Y-%m-%dT%H:%M')
    deadline2 = datetime.strptime(body['deadline2'], '%Y-%m-%dT%H:%M')
    deadline3 = datetime.strptime(body['deadline3'], '%Y-%m-%dT%H:%M')
    deadline4 = datetime.strptime(body['deadline4'], '%Y-%m-%dT%H:%M')
    step1_pwd = body['step1_pwd']
    step2_pwd = body['step2_pwd']

    # if deadline0 > deadline1 or deadline1 > deadline2 or deadline2 > deadline3 or deadline3 > deadline4:
    #     return { "message" : "Quiz settings were not saved because of invalid deadlines", "redirect": url_for("pages.quiz_configuration", q = q)}, 400

    q.deadline0 = deadline0
    q.deadline1 = deadline1
    q.deadline2 = deadline2
    q.deadline3 = deadline3
    q.deadline4 = deadline4
    q.step1_pwd = step1_pwd
    q.step2_pwd = step2_pwd
    q.deadline_driven = "True"

    if deadline0 > deadline1 or deadline1 > deadline2 or deadline2 > deadline3 or deadline3 > deadline4:
        flash("Quiz settings were not saved because of invalid deadlines", "error")
        return render_template('quiz-configuration.html', quiz = q.dump_as_dict())

    models.DB.session.commit()

    return { "message" : "Quiz settings were saved", "redirect": url_for("pages.quiz_configuration", q = q)}, 200

def get_possible_justifications(attempt):
    '''
    Collect all possible justifications from which policy should pick 
    :param attempt - student attempt for quiz
    '''
    qids = [ int(qid) for qid in attempt.alternatives_map.keys() ]
    dids = set(did for _, alternatives in attempt.alternatives_map.items() for did in alternatives)
    did_positions = {(int(qid), did):aid for qid, alternatives in attempt.alternatives_map.items() for aid, did in enumerate(alternatives)}
    justification_plain = models.Justification.query.where(models.Justification.quiz_question_id.in_(qids), 
            models.Justification.distractor_id.in_(dids), models.Justification.ready==True,
            not_(models.Justification.student_id == current_user.id),
            not_(models.Justification.justification==""), not_(models.Justification.justification=="<br>"),
            not_(models.Justification.justification=="<p><br></p>"), not_(models.Justification.justification=="<p></p>")).all()
    justifications = {str(qid):{str(did_positions[(qid, did)]):djs for did, djs in groupby(js, key=lambda x:x.distractor_id)} 
                        for qid, js in groupby(justification_plain, key=lambda x: x.quiz_question_id)}
    return justifications

#See discussion of policies on overleaf
def pick_without_replacement(justifications, index):
    neo = justifications.pop(index)
    neo.seen = neo.seen + 1
    return neo
    
#NOTE: signature of this function corresponds to signature of policy 
# - pool of justifications, id of slot to which they are picked and max number of slots
def j_random(justifications, slot_id, max_slots):
    index = random.randint(0, len(justifications) - 1)
    return pick_without_replacement(justifications, index)

def j_not_seen(not_seen_n_times = 1, not_seen_policy = j_random, seen_policy = j_random):
    '''
    prefers first not seen yet justififcations and then apply inner getter 
    :param getter - inner policy which is select_random_justification by default
    '''
    assert(not_seen_n_times >= 1) #number of seen required should be positive
    def policy(justifications, slot_id, max_slots):    
        not_seen_justification = [ j for j in justifications if j.seen < not_seen_n_times ]
        if any(not_seen_justification):
            neo = not_seen_policy(not_seen_justification, slot_id, max_slots)
            justifications.remove(neo)
            return neo
        else:
            return seen_policy(justifications, slot_id, max_slots)
    return policy

def j_least_seen(inner_policy = j_random):
    def policy(justifications, slot_id, max_slots):
        assert(len(justifications) > 0)
        one_min_seen_j = min(justifications, key=lambda j: j.seen)    
        min_seen_justifications = [ j for j in justifications if j.seen == one_min_seen_j.seen ]
        selected = inner_policy(min_seen_justifications, slot_id, max_slots)
        justifications.remove(selected)
        return selected 
    return policy

# selections from https://cdn.discordapp.com/attachments/773018086114590721/973348013655343124/Whiteson_-_2006_-_OEA.pdf
def j_e_greedy(epsilon, fitness, best_policy = j_random, other_policy = j_random):
    '''
    Builder of epsilon-greedy policy where which chance epsilon the best justification based on quality will be taken 
    Otherwise, fallback_policy will be applied 
    '''
    def policy(justifications, slot_id, max_slots):
        level = random.random()
        if level < epsilon: 
            j_with_f = [ (j, fitness(j)) for j in justifications ]
            (_, best_fitness) = max(j_with_f, key=lambda j: j[1])
            best_justfications = [j for (j, f) in j_with_f if f == best_fitness]
            neo = best_policy(best_justfications, slot_id, max_slots)
            justifications.remove(neo)
            return neo 
        else:
            return other_policy(justifications, slot_id, max_slots)
    return policy

def j_slot_group_till(edge_id_excluded = 1, in_group_policy = j_random, out_group_policy = j_random):
    assert(edge_id_excluded > 0)
    def policy(justifications, slot_id, max_slots):
        if slot_id < edge_id_excluded:
            return in_group_policy(justifications, slot_id, max_slots)
        else:
            return out_group_policy(justifications, slot_id, max_slots)
    return policy

def j_softmax(temperature, fitness):
    '''
    implements softmax policy builder 
    temperature could be constant or function (for anealing)
    '''
    if not callable(temperature):
        temperature = lambda: temperature
    def policy(justifications, slot_id, max_slots):
        j_with_f = [ (j, fitness(j)) for j in justifications ]
        t = temperature()
        j_with_p = [ (j, exp(f) / t) for (j, f) in j_with_f ]
        total = sum(p for (_, p) in j_with_p)
        # j_with_p = [ (j, p / total) for (j, p) in j_with_p ]
        for (j, p) in j_with_p:
            level = random.random()
            if level < p / total: 
                neo = j
                neo.seen = neo.seen + 1 
                justifications.remove(neo)
                return neo 
            else:
                total = total - p
    return policy 

# NOTE: cannot dev this due to deterministic nature of fitness in our case at moment of selection
# def interval_estimation(uncertainty, fitness):
#     '''
#     uses uncertainty interval
#     https://cdn.discordapp.com/attachments/773018086114590721/973348013655343124/Whiteson_-_2006_-_OEA.pdf
#     Algo 3
#     '''
#     def policy(justifications):
#               ....        
#     return policy 

# classic EA selections 

def j_fitness_proportional(fitness):
    def policy(justifications, slot_id, max_slots):
        j_with_f = [ (j, fitness(j)) for j in justifications]
        total = sum(f for (_, f) in j_with_f)
        level = random.random() * total 
        upLevel = 0
        for (j, f) in j_with_f:
            upLevel = upLevel + f 
            if upLevel > level:
                neo = j 
                neo.seen = neo.seen + 1
                justifications.remove(neo)
                return neo                 
    return policy 

def j_tournament(k, fitness):
    def policy(justifications, slot_id, max_slots):
        size = k(justifications) if callable(k) else k
        j_with_f = [ (j, fitness(j)) for j in justifications]
        candidates = [ random.choice(j_with_f) for i in range(min(len(justifications), size)) ]
        (neo, _) = max(candidates, key = lambda j: j[1])
        neo.seen = neo.seen + 1
        justifications.remove(neo)
        return neo
    return policy 
    

def select_justifications(justifications, num_slots, selection_policy = j_random): 
    ''' This is where we apply the peer selection policy
        :param justifications - list of all justififcations
        :param num_justifications_shown - wanted number per quiz 
    '''
    # 
    # We now revisit the data we collected and pick one justification in each array of Justification objects    
    res = {}
    for (qid, distractors) in justifications.items():
        res[qid] = {}
        for (did, js) in distractors.items():            
            if (len(js) <= num_slots):
                res[qid][did] = js #TODO: order still could metter
            else:
                cloned = js[:]
                selected = [ selection_policy(cloned, slot_id, num_slots) for slot_id in range(num_slots) ]
                res[qid][did] = selected
    return res

@pages.route('/quiz/<int:quiz_id>/<int:course_id>/justification/histogram', methods=['GET'])
@login_required 
def get_justification_distribution(quiz_id, course_id):
    ''' outputs png for shown justification distribution '''
    if not current_user.is_instructor():
        flash("You are not allowed to get justification distribution")
        return redirect(url_for('pages.index'))
    attempt_quality_attr = request.args.get("attempt_quality", "initial_total_score")   
    def attempt_quality(attempt):
        return getattr(attempt, attempt_quality_attr)    
    attempts = models.QuizAttempt.query.filter(models.QuizAttempt.quiz_id == quiz_id, models.QuizAttempt.status != QUIZ_ATTEMPT_STEP1, models.QuizAttempt.course_id == course_id).all() # assuming one per student for now 
    quiz_attempt_ids = set(a.id for a in attempts)
    student_attempts = {a.student_id: a for a in attempts} #TODO: one attempt per student per quiz currently 
    # attempt_map = {a.id:a for a in attempts}
    # questions = models.Question.query.filter_by(quiz_id=quiz_id).with_entities(models.Question.id, models.Question.id).all()
    attempt_justifications = DB.session.query(models.attempt_justifications).where(models.attempt_justifications.c.attempt_id.in_(quiz_attempt_ids)).all()    
    justification_ids = set(j_id for (_, j_id) in attempt_justifications)
    # justifications = models.Justification.query.where(models.Justification.id.in_(justification_ids)).with_entities(models.Justification.student_id).all()
    justifications = models.Justification.query.where(models.Justification.id.in_(justification_ids)).all()
    # justification_student_ids = set(j.student_id for j in justifications)

    def justification_fitness(justification):
        justification_attempt = student_attempts[justification.student_id]
        return attempt_quality(justification_attempt)
    j_with_p = [(j, justification_fitness(j)) for j in justifications]
    j_with_p.sort(key=lambda j: j[1])
    justification_histogram = [j.seen for (j, _) in j_with_p]
    tick_label = [str(f) for (_, f) in j_with_p]
    prev = None 
    for i in range(len(tick_label)):
        if prev is None:
            prev = tick_label[i]
        elif prev == tick_label[i]:
            tick_label[i] = None 
        else:
            prev = tick_label[i]

    figure = plt.figure(figsize=[12.8, 4.8])
    try:
        # figure.gca().hist(justification_histogram, bins=len(justification_histogram), weights=justification_histogram)
        figure.gca().bar(range(len(justification_histogram)), justification_histogram, width=1, align='edge', tick_label=tick_label)
        bytes = io.BytesIO()
        figure.savefig(bytes, format='png')
        bytes.seek(0)
        return send_file(bytes, as_attachment = False, mimetype = 'image/png')
    finally:
        plt.close(figure)

def get_or_create_attempt(quiz: models.Quiz, course, quiz_questions, distractor_per_question):
    attempt = models.QuizAttempt.query.filter_by(student_id=current_user.id, quiz_id=quiz.id, course_id=course.id).first()
    if attempt is None: #first visit 
        quiz_model = get_quiz_builder().load_quiz_model(quiz, create_if_not_exist=True)
        if quiz_model is None: #by default when no evo process - we pick all distractors selected by instructor
            selected_distractor_ids = [{"question_id": qq.id, "alternatives": [d.id for d in distractor_per_question.get(qq.question_id, [])] } 
                                        for qq in quiz_questions]
        else: #rely on evo engine for selection of distractors
            selected_distractor_ids = [{"question_id": qid, "alternatives": ds} 
                                        for qid, ds in quiz_model.get_for_evaluation(current_user.id)]
        for question_alternatives in selected_distractor_ids:
            question_alternatives["alternatives"].append(-1) #add correct answer 
            random.shuffle(question_alternatives["alternatives"]) #shuffle each question alternatives
        attempt = models.QuizAttempt(quiz_id=quiz.id, student_id=current_user.id, status = QUIZ_ATTEMPT_STEP1, alternatives=selected_distractor_ids, course_id=course.id)
        models.DB.session.add(attempt)
        models.DB.session.commit()
    return attempt

@pages.route('/student/<quiz:quiz_course>', methods=['GET']) #IMPORTANT: see the notation of <quiz:q> in the url template - these are custom converter - check _init__.py APP.url_map.converters 
@login_required
@role_required(role=ROLE_STUDENT, redirect_route='pages.index', redirect_message="You are not allowed to take this quiz")
@verify_deadline(quiz_attempt_param = "quiz_course", redirect_route='pages.index')
@verify_instructor_relationship(quiz_attempt_param = "quiz_course", redirect_route='pages.index')
@retry_concurrent_update #this will retry the call of this function  in case when two requests try to update db at same time - optimistic concurency 
def get_quiz(quiz_course):
    '''
    Links using this route are meant to be shared with students so that they may take the quiz
    and engage in the asynchronous peer instrution aspects. 
    '''
    # TODO #3 we replace dump_as_dict with proper Markup(...).unescape of the objects'fields themselves
    # see lines commented out a ## for originals
    ##quiz_questions = [question.dump_as_dict() for question in q.quiz_questions]
    q = quiz_course.quiz
    course = quiz_course.course
    quiz_questions = q.quiz_questions
    # FIXME why are we not unescaping above?

    # BUG we had to simplify the questions to avoid an escaping problem
    # simplified_quiz_questions = [question.dump_as_simplified_dict() for question in q.quiz_questions]    
    # PBM - the alternatives for questions show unescaped when taking the quiz
    # SOL - need to unescape them before to pass them to the template
    
    ##for qq in quiz_questions:
    ##    for altern in qq["alternatives"]:
    ##        # experimenting, this works: tmp = unescape(quiz_questions[0]["alternatives"][0][1])
    ##        altern[1] = unescape(altern[1])
    ##        # nope... altern[1] = jinja2.Markup.escape(altern[1])

    quiz_question_ids = set(q.id for q in quiz_questions)
    quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(quiz_question_ids)).all()
    distractor_ids = [d.distractor_id for d in quiz_question_distractors]
    plain_distractors = models.Distractor.query.where(models.Distractor.id.in_(distractor_ids))
    distractor_per_question = {q_id: ds for q_id, ds in groupby(plain_distractors, key = lambda d: d.question_id)}    
    distractor_map = {d.id:d for d in plain_distractors}

    #unescaping part - left for backward compatibility for now
    
    attempt = get_or_create_attempt(q, course, quiz_questions, distractor_per_question)
    quiz_question_ids = [ int(qid) for qid in attempt.alternatives_map.keys() ]
    question_ids = [ qq.question_id for qq in quiz_questions ]
    # student created distractors where ids are in quiz_question_ids
    student_created_distractors = models.InvalidatedDistractor.query.where(models.InvalidatedDistractor.question_id.in_(question_ids), models.InvalidatedDistractor.author_id == current_user.id).all()
    student_created_distractors = {d.question_id:d for d in student_created_distractors}
    distractor_ids = [did for _, ds in attempt.alternatives_map.items() for did in ds]

    justifications = models.Justification.query.where(models.Justification.quiz_question_id.in_(quiz_question_ids), models.Justification.distractor_id.in_(distractor_ids), models.Justification.student_id == current_user.id).all()
    justification_map = {qid:{j.distractor_id:j for j in js} for qid, js in groupby(justifications, key=lambda x:x.quiz_question_id)}

    question_model = [ { "id": qq.id, 
                        "alternatives": [ unescape(distractor_map[alternative].answer) if alternative in distractor_map else unescape(qq.question.answer) 
                                                for alternative in attempt.alternatives_map[str(qq.id)]
                                                if alternative in distractor_map or alternative == -1],
                        "choice": next((i for i, d in enumerate(attempt.alternatives_map[str(qq.id)]) if d == attempt.step_responses.get(str(qq.id), None)), -1), 
                        "invalidated_distractors": student_created_distractors,
                        "justifications": {a:js[did].justification for a, did in enumerate(attempt.alternatives_map[str(qq.id)]) if did in js},
                        **{attr:unescape(getattr(qq.question, attr)) for attr in [ "title", "stem", "answer" ]}}
                        for qq in quiz_questions
                        if str(qq.id) in attempt.alternatives_map
                        # for (qq, alternatives) in zip(quiz_questions, attempt.alternatives) 
                        for js in [justification_map.get(qq.id, {})]]

    quiz_model = { "id" : q.id, "title" : q.title, "description" : q.description, "deadline0": q.deadline0, "deadline1": q.deadline1, "deadline2": q.deadline2, "deadline3": q.deadline3, "deadline4": q.deadline4 } #we do not need any other fields from dump_as_dict
    #NOTE: dump_as_dict causes additional db requests due to rendering related entities.

    def check_quiz_session_cookie():
        return "quiz_session_id" in request.cookies and request.cookies["quiz_session_id"] == f"{current_user.id}:{q.id}"
    def reset_quiz_session_cookie(resp: Response):
        # resp.set_cookie('quiz_session_id', '', expires=0)
        return resp    
    if not check_quiz_session_cookie():
        return redirect(url_for("pages.protected_get_quiz", q = q))    
    if attempt.status == QUIZ_ATTEMPT_STEP1:
        return reset_quiz_session_cookie(make_response(render_template('step1.html', quiz=quiz_model, questions=question_model, course=course)))
    if attempt.status == QUIZ_ATTEMPT_STEP2:
        if attempt.selected_justifications_timestamp is None: #attempt justifications were not initialized yet
            # retrieve the peers' justifications for each question  
            possible_justifications = get_possible_justifications(attempt)

            # This is where we apply the peer selection policy
            # selected_justification_map = select_justifications(possible_justifications, q.num_justifications_shown, \
            #     selection_policy = \
            #         not_seen_justification_and(not_seen_n_times=1, \
            #             not_seen_policy = select_random_justification, \
            #             fallback_policy = \
            #                 not_seen_justification_and(not_seen_n_times=2, \
            #                     not_seen_policy = select_random_justification, \
            #                     fallback_policy = select_random_justification) ))

            student_ids = set(j.student_id for (_, d) in possible_justifications.items() for (_, js) in d.items() for j in js)
            attempts = models.QuizAttempt.query.filter_by(quiz_id = q.id, course_id=course.id).where(models.QuizAttempt.student_id.in_(student_ids)).all()
            student_attempts = {a.student_id:a for a in attempts}

            def get_justification_fitness(justification):
                return student_attempts[justification.student_id].initial_total_score

            # selected_justification_map = select_justifications(possible_justifications, q.num_justifications_shown, \
            #     selection_policy = \
            #         not_seen_justification_and(not_seen_n_times=1, \
            #             not_seen_policy = select_random_justification, \
            #             fallback_policy = tournament(7, fitness=get_justification_fitness)))       
            #
                
            # selected_justification_map = select_justifications(possible_justifications, q.num_justifications_shown, \
            #     selection_policy = \
            #         not_seen_justification_and(not_seen_n_times=1, \
            #             not_seen_policy = select_random_justification, \
            #             fallback_policy = epsilon_greedy(0.25, \
            #                 best_policy=select_random_justification, \
            #                 fallback_policy=select_random_justification, \
            #                 fitness=get_justification_fitness)))

            num_in_group = get_least_seen_slots_num(q.num_justifications_shown)
            selected_justification_map = select_justifications(possible_justifications, q.num_justifications_shown, \
                selection_policy = j_slot_group_till(num_in_group,\
                    in_group_policy=j_least_seen(j_random), \
                    out_group_policy=\
                        j_tournament(get_k_tournament_size, fitness=get_justification_fitness)))
                        # j_e_greedy(0.2, fitness=get_justification_fitness, best_policy=j_random, other_policy=j_random)))
                        # j_fitness_proportional(fitness=get_justification_fitness)))

            attempt.selected_justifications.extend(j for d in selected_justification_map.values() for js in d.values() for j in js)

            attempt.max_likes = sum(len(js) for d in selected_justification_map.values() for js in d.values())
            attempt.participation_grade_threshold = round(attempt.max_likes * q.limiting_factor)
            #Idea: put another select to check if we have someting for this attempt id 
            attempt.selected_justifications_timestamp = datetime.now()
            models.DB.session.commit()
        else: 
            #justification list to map
            # selected_justification_map = {}
            selected_justifications = attempt.selected_justifications #here db query for selected justififcations
            selected_justifications_question_ids = set(str(j.quiz_question_id) for j in selected_justifications)
            selected_justifications_distractor_ids = set(str(j.distractor_id) for j in selected_justifications)
            selected_justification_map = {qid:{did:[] for did in selected_justifications_distractor_ids} for qid in selected_justifications_question_ids}
            for j in selected_justifications:
                selected_justification_map[str(j.quiz_question_id)][str(j.distractor_id)].append(j)
        
        jids = set(j.id for j in attempt.selected_justifications)
        present_likes = models.Likes4Justifications.query.where(models.Likes4Justifications.student_id == current_user.id,
            models.Likes4Justifications.justification_id.in_(jids)).all()
            
        likes = set(l.justification_id for l in present_likes)
        return reset_quiz_session_cookie(make_response(render_template('step2.html', quiz=quiz_model, course=course,
            questions=question_model, attempt=attempt.dump_as_dict(),
            justifications=selected_justification_map, likes = likes)))

    # finding the reference justifications for each distractor
    explanations = {qid:{str(aid):{"justification": "Correct answer!" if did == -1 else unescape(distractor_map[did].justification), "is_correct": did == -1 } 
                        for aid, did in enumerate(alternatives) if did in distractor_map or did == -1}
                    for qid, alternatives in attempt.alternatives_map.items()}
    
    if attempt.status == QUIZ_ATTEMPT_STEP3:
        return render_template('step3.html', quiz=quiz_model, course=course,
            questions=question_model, attempt=attempt.dump_as_dict(), explanations=explanations)
    
    #else status is SOLUTIONS
    return reset_quiz_session_cookie(make_response(render_template("solutions.html", quiz=quiz_model,
        questions=question_model, attempt=attempt.dump_as_dict(), explanations=explanations)))

@pages.route('/student/<quiz:quiz_course>/start', methods=['GET', 'POST'])
@login_required
@role_required(role=ROLE_STUDENT, redirect_route='pages.index', redirect_message="You are not allowed to take this quiz")
@verify_deadline(quiz_attempt_param = "quiz_course", redirect_route='pages.index')
@verify_instructor_relationship(quiz_attempt_param = "quiz_course", redirect_route='pages.index')
def protected_get_quiz(quiz_course):
    '''
    Same to get_quiz but requires login password from student. Instead of GET, POST method is used. 
    This method is entered when student submit login form 
    '''
    q = quiz_course.quiz
    course = quiz_course.course
    step_pwd = q.step1_pwd if q.status == QUIZ_STEP1 else q.step2_pwd if q.status == QUIZ_STEP2 else ""
    if step_pwd != "":
        if request.method == 'GET':
            return render_template('honorlock.html', quiz = q)
        password = request.form.get('password')
        if password != step_pwd:
            flash('Incorrect pass phrase was provided.')
            return redirect(url_for('pages.protected_get_quiz', quiz_course = quiz_course))

    response = make_response(redirect(url_for("pages.get_quiz", quiz_course = quiz_course)))
    response.set_cookie('quiz_session_id', f"{current_user.id}:{q.id}")
    return response

@pages.route('/student/<qa:q>', methods=['POST']) #IMPORTANT: see the notation of <qa:q> in the url template - these are custom converter - check _init__.py APP.url_map.converters 
@login_required
@role_required(role=ROLE_STUDENT, redirect_route='pages.index', redirect_message="You are not allowed to take this quiz")
@verify_deadline(quiz_attempt_param = "q", redirect_route='pages.index')
@verify_instructor_relationship(quiz_attempt_param = "q", redirect_route='pages.index')
@validate_quiz_attempt_step(quiz_attempt_param = "q")
@unmime(delim='_', type_converters={"question":{"*":lambda x: int(x)}})
@retry_concurrent_update
def save_quiz_attempt(q, body):
    quiz, course, attempt = q

    body.setdefault("question", {})    

    answer_questions(q, body["question"])
    #validation that attempt could go to next step 
    for qid in attempt.alternatives_map.keys():
        if qid not in attempt.step_responses:
            return {"message": "You must select an answer for each question", "redirect": url_for("pages.get_quiz", quiz_course = q) }, 400
        
    response_set = {(int(qid), did) for qid, did in attempt.step_responses.items()}

    if attempt.status == QUIZ_ATTEMPT_STEP1:
        # if not (date > quiz.deadline0 and date <= quiz.deadline1):
        #     models.QuizAttempt.query.filter_by(student_id=current_user.id).delete()
        #     models.DB.session.commit()
        #     flash("You missed the deadline for Step1.", "error")
        #     return redirect(url_for('pages.index'))
        body.setdefault("justification", {})
        justify_alternative_selection(q, body["justification"])

        quiz_question_ids = [ int(qid) for qid in attempt.alternatives_map.keys() ]
        saved_justifications = models.Justification.query.where(models.Justification.quiz_question_id.in_(quiz_question_ids), models.Justification.student_id == current_user.id).all()
        js_map = {(j.quiz_question_id, j.distractor_id): j for j in saved_justifications}
        #check that for all alternatives justifications were provided 
        js_to_delete = []
        for qid, alternatives in attempt.alternatives_map.items():
            qid = int(qid)
            for did in alternatives:
                qdid = (qid, did)
                if qdid in response_set:
                    if qdid in js_map:
                        js_to_delete.append(js_map[qdid])
                elif qdid not in js_map:
                    return { "message" : "You must provide a justification for each unselected option", "redirect": url_for("pages.get_quiz", quiz_course=q) }, 400
                else:
                    js_map[qdid].ready = True #justification could be used by student on next step

        #justifications were validated - we delete unnecessary justifications (for selected answers)
        if hasattr(g, "allow_justification_for_selected") and g.allow_justification_for_selected:
            for qdid in js_map:
                js_map[qdid].ready = True #for testing purpose
        else:
            for j in js_to_delete:
                models.DB.session.delete(j)

        attempt.revised_responses = attempt.initial_responses

        quiz_model = get_quiz_builder().load_quiz_model(quiz)
        if quiz_model is not None: 
            answers = { int(q_id): answer for q_id, answer in attempt.initial_responses.items() }
            quiz_model.evaluate(current_user.id, answers)
    elif attempt.status == QUIZ_ATTEMPT_STEP3:
        for quiz_question in quiz.quiz_questions:
            student_created_distractor = models.InvalidatedDistractor.query.filter_by(question_id=quiz_question.question_id, author_id=current_user.id).first()
            if student_created_distractor is None or student_created_distractor.answer == "" or student_created_distractor.justification == "":
                return { "message" : "You must provide a distractor and justification for each question", "redirect": url_for("pages.get_quiz", quiz_course=q) }, 400

        # get question ids from the quiz questions
        question_ids = [question.question_id for question in quiz.quiz_questions]
        
        # get the student's distractors for the question ids
        student_distractors = models.InvalidatedDistractor.query.filter_by(author_id=current_user.id).where(models.InvalidatedDistractor.question_id.in_(question_ids)).all()

        # change the status of the distractors
        for distractor in student_distractors:
            distractor.status = "complete"


    if quiz.step3_enabled == "True" and attempt.status == QUIZ_ATTEMPT_STEP2:
        attempt.status = QUIZ_ATTEMPT_STEP3
    else: 
        attempt.status = get_attempt_next_step(attempt.status)     

            
    models.DB.session.commit()
    
    if attempt.status == QUIZ_ATTEMPT_STEP3:
        return {"message": "Quiz sumbission was saved!", "redirect": url_for("pages.get_quiz", quiz_course=q) }
    
    return {"message": "Quiz sumbission was saved!", "redirect": url_for("pages.index") }

@pages.route('/users/', methods=['GET'])
@login_required
def users_browser():
    '''
    This page allows to manage all user accounts on the system.
    '''
    if not current_user.is_admin():
        flash("Restricted to admins.", "error")
        return redirect(url_for('pages.index'))
    all_users = models.User.query.all()
    return render_template('users-browser.html', all_users=all_users)

#NOTE: no model data should be present on UI
@dataclass
class QuizStats:
    quiz: dict # 1 level dict: props, one quiz with name-value props
    course: dict # 1 level dict: props, one course with name-value props
    questions: dict # 2 level dict: question_id: props. key question_id and value is another dict 
    distractors: dict # 3 level dict: question_id:distractor_id:props
    students: list # list of quiz students: list of props
    # attempts: dict # 2 level student_id: props
    # likes_given: dict # 1 level: student_id: list of justification props
    # likes_received: dict # 1 level - similar to prev
    # justification_like_count: dict #3 level: question_id:distractor_id:justification_text:count
    # justification_scores: dict #dict student id: score 
    # total_perecent_score: dict #dict student id: score 

def get_quiz_statistics(qid, course_id):
    '''
    This page allows to get all stats on a given quiz.
    '''    
    quiz = models.Quiz.query.get_or_404(qid)
    course = models.Course.query.get_or_404(course_id)

    quiz_questions = quiz.quiz_questions
    question_ids = set(qu.question_id for qu in quiz_questions)
    quiz_question_ids = set(qu.id for qu in quiz_questions)
    plain_questions = models.Question.query.where(models.Question.id.in_(question_ids)).all()
    questions = {q.id:{**q.dump_as_simplified_dict(), **{attr:unescape(getattr(q, attr)) 
                                                            for attr in ["stem", "answer", "title"]} } 
                    for q in plain_questions}

    quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(quiz_question_ids)).all()
    distractor_ids = [d.distractor_id for d in quiz_question_distractors]
    plain_distractors = models.Distractor.query.where(models.Distractor.id.in_(distractor_ids)).all()
    distractors = { qid : {d.id : unescape(d.answer) for d in ds} 
                    for (qid, ds) in groupby(plain_distractors, key = lambda d: d.question_id) } 

    plain_attempts = models.QuizAttempt.query.where(models.QuizAttempt.quiz_id == qid, models.QuizAttempt.status != QUIZ_ATTEMPT_STEP1, models.QuizAttempt.course_id == course_id).all()

    quiz_questions = {}
    quiz_question_distractors = {}
    for (question_id, quiz_question_id) in zip(question_ids, quiz_question_ids):
        quiz_questions[quiz_question_id] = questions[question_id]
        quiz_question_distractors[quiz_question_id] = distractors[question_id]

    stats = QuizStats(quiz.dump_as_dict(), course.dump_as_dict(), quiz_questions, quiz_question_distractors, students = [])

    if len(plain_attempts) == 0:
        return stats  
    attempts_map = {a.student_id: a for a in plain_attempts} #assume 1 attempt for 1 student - otherwise use other grouping
        
    student_ids = attempts_map.keys()        
    plain_justifications = models.Justification.query.where(models.Justification.student_id.in_(student_ids), 
                                models.Justification.quiz_question_id.in_(quiz_question_ids)).all()
    justification_map = {j.id:j.dump_as_dict() for j in plain_justifications}

    plain_likes = models.Likes4Justifications.query.where(models.Likes4Justifications.student_id.in_(student_ids)).all()
    likes_given = { **{ a.student_id: [] for a in plain_attempts if a.status == QUIZ_ATTEMPT_SOLUTIONS  },
                    **{ student_id: [justification_map[l.justification_id] for l in student_likes if l.justification_id in justification_map] 
                        for student_id, student_likes in groupby(plain_likes, key = lambda like: like.student_id) }}
    
    like_scores = { a.student_id: sum(parts)
        for a in plain_attempts 
        for parts in [[justifications_liked_by_o_to_a * min(participation_threshold_of_o / max(len(given_likes_by_o), 1), 1) 
                for o in plain_attempts if a.student_id != o.student_id and o.student_id in likes_given
                for given_likes_by_o in [likes_given.get(o.student_id, [])]
                for participation_threshold_of_o in [ quiz.limiting_factor * o.max_likes ]
                for justifications_liked_by_o_to_a in [sum(1 for j in given_likes_by_o if j["student_id"] == a.student_id)]]]
        if len(parts) > 0 or a.status == QUIZ_ATTEMPT_SOLUTIONS}            
        
    def decide_grades(quiz, score, ranges):
        for (r, quartile) in zip(ranges, [quiz.fourth_quartile_grade, quiz.third_quartile_grade, quiz.second_quartile_grade]):
            if score >= r:
                return quartile
        return quiz.first_quartile_grade  

    sorted_scores = list(like_scores.values())
    sorted_scores.sort()    
    if len(sorted_scores) > 0:
        median, median_indices = find_median(sorted_scores)
        q1, _ = find_median(sorted_scores[:median_indices[0]])
        q3, _ = find_median(sorted_scores[median_indices[-1] + 1:])
        quartiles = [median if q3 is None else q3, median, 0 if q1 is None else q1]
        justification_scores = {a.student_id: decide_grades(quiz, like_scores[a.student_id], quartiles) 
            for a in plain_attempts if a.student_id in like_scores }
    else:
        justification_scores = {}
    
    student_justifications = [{**justification_map[justification_id], 
                                "num_likes": len(list(students_who_like))}
                        for justification_id, students_who_like in groupby(plain_likes, key = lambda like: like.justification_id) 
                        if justification_id in justification_map]
    likes_received = {**{ a.student_id: [] for a in plain_attempts if a.status != QUIZ_ATTEMPT_STEP1  },
                        **{student_id: list(js) for student_id, js in groupby(student_justifications, key=lambda j: j["student_id"])}}
    
    justification_like_count = {student_id:{j["justification"]:j["num_likes"] for j in student_js} for student_id, student_js in likes_received.items()}

    #designing score compute 
    invalidated_distractors_plain = models.InvalidatedDistractor.query.where(models.InvalidatedDistractor.author_id.in_(student_ids), models.InvalidatedDistractor.question_id.in_(question_ids)).all()
    designing_grades = {student_id:0 if len(designed_distractors) == 0 else (sum(d.grade for d in designed_distractors) / len(designed_distractors)) 
                            for student_id, designed_distractors in groupby(invalidated_distractors_plain, key=lambda x: x.author_id)}

    #compute total scores 
    max_justfication_grade = max(quiz.first_quartile_grade, quiz.second_quartile_grade, quiz.third_quartile_grade, quiz.fourth_quartile_grade)
    percent_scores = {}
    cetagory_percent_scores = {}
    participation_scores = {}
    designing_scores = {}
    for attempt in plain_attempts:    
        sid = attempt.student_id
        if len(attempt.initial_responses) > 0:
            student_initial_score = attempt.initial_total_score
            student_max_initial_score = len(attempt.initial_responses)
            cetagory_percent_scores.setdefault(sid, {}).setdefault("initial", (student_initial_score / student_max_initial_score, quiz.initial_score_weight))
        if attempt.status == QUIZ_ATTEMPT_SOLUTIONS or attempt.status == QUIZ_STEP3:
            student_revised_score = attempt.revised_total_score
            student_max_revised_score = len(attempt.revised_responses)
            student_max_revised_score = 1 if student_max_revised_score == 0 else student_max_revised_score
            cetagory_percent_scores.setdefault(sid, {}).setdefault("revised", (student_revised_score / student_max_revised_score, quiz.revised_score_weight))
        if sid in justification_scores:
            student_justification_score = justification_scores[sid]
            student_max_justification_score = max_justfication_grade
            cetagory_percent_scores.setdefault(sid, {}).setdefault("justification", (student_justification_score / student_max_justification_score, quiz.justification_grade_weight))
        if sid in likes_given:
            likes_given_length = len(likes_given[sid])
            participation_scores[sid] = 1 if likes_given_length >= round(attempt.get_min_participation_grade_threshold()) and likes_given_length <= attempt.participation_grade_threshold else 0
            student_participation_score = participation_scores[sid]
            student_max_participation_score = 1
            cetagory_percent_scores.setdefault(sid, {}).setdefault("participation", (student_participation_score / student_max_participation_score, quiz.participation_grade_weight))   
        if sid in designing_grades:
            designing_scores[sid] = designing_grades[sid]
            student_design_score = designing_scores[sid]
            student_max_design_score = 100
            cetagory_percent_scores.setdefault(sid, {}).setdefault("designing", (student_design_score / student_max_design_score, quiz.designing_grade_weight))
        grades = [grade for grade in cetagory_percent_scores.get(sid, {}).values()]
        percents, weights = ([], []) if len(grades) == 0 else tuple(zip(*grades)) #unzip 
        # weights should sum up to 100 - so in case when some of grades are not available - we rescale 
        total_weights = sum(weights) 
        total_weights = 1 if total_weights == 0 else total_weights
        weights = [ w / total_weights for w in weights ]
        percent_scores[sid] = sum(w * p for w, p in zip(weights, percents))
    
    plain_students = models.User.query.where(models.User.id.in_(student_ids)).order_by(collate(models.User.last_name, 'NOCASE')).all()
    student_ids = set(s.id for s in plain_students)
    
    justifications_by_student = {sid: js for sid, js in groupby(plain_justifications, key = lambda x: x.student_id)}
    
    roundNotNone = lambda v: v if v is None else (round(v[0], 2) * 100)
    
    stats.students = [{**a.dump_as_dict(), **s.dump_as_dict(), 
                        "likes_given": likes_given.get(s.id, None),
                        "likes_given_count": len(likes_given[s.id]) if s.id in likes_given else None,
                        "like_score": like_scores.get(s.id, None),
                        "initial_total_score": a.initial_total_score if len(a.initial_responses) > 0 else None,
                        "revised_total_score": a.revised_total_score if a.status == QUIZ_ATTEMPT_SOLUTIONS or a.status == QUIZ_STEP3 else None,
                        "justification_score": justification_scores.get(s.id, None),
                        "max_justification_score": quiz.fourth_quartile_grade,
                        "likes_received": likes_received.get(s.id, None),
                        "likes_received_count": sum(j["num_likes"] for j in likes_received[s.id]) if s.id in likes_received else None,
                        "justification_like_count": justification_like_count.get(s.id, {}),
                        "min_participation_grade_threshold": int(a.get_min_participation_grade_threshold()) if a.status == QUIZ_ATTEMPT_SOLUTIONS or a.status == QUIZ_STEP3 else None,
                        "participation_grade_threshold": int(a.participation_grade_threshold) if a.status == QUIZ_ATTEMPT_SOLUTIONS or a.status == QUIZ_STEP3 else None,
                        "participation_score": int(participation_scores[s.id]) if s.id in participation_scores else None,
                        "designing_score": int(designing_scores[s.id]) if s.id in designing_scores else None,
                        "initial_responses": {int(k):v for k, v in a.initial_responses.items()},
                        "revised_responses": {int(k):v for k, v in a.revised_responses.items()},
                        # "justifications": ast.literal_eval(unescape(a.justifications).replace("\\n", "a").replace('\\"', '\"')),
                        "justifications": {qid: {j.distractor_id:j.justification for j in js} for qid, js in groupby(justifications_by_student.get(s.id, []), key = lambda x: x.quiz_question_id)
                                                if str(qid) in a.alternatives_map},
                        "initial_percent": roundNotNone(cetagory_percent_scores.get(s.id, {}).get("initial", None)),
                        "revised_percent": roundNotNone(cetagory_percent_scores.get(s.id, {}).get("revised", None)),
                        "justfication_percent": roundNotNone(cetagory_percent_scores.get(s.id, {}).get("justification", None)),
                        "participation_percent": roundNotNone(cetagory_percent_scores.get(s.id, {}).get("participation", None)),
                        "designing_percent": roundNotNone(cetagory_percent_scores.get(s.id, {}).get("designing", None)),
                        "total_percent": student_percent_score * 100}
                        for s in plain_students 
                        if s.id in attempts_map 
                        for a, student_percent_score in [(attempts_map[s.id], 
                            round(percent_scores[s.id], 2) if s.id in percent_scores else None)]]

    return stats

@pages.route('/quiz/<int:qid>/<int:course_id>/grades', methods=['GET'])
@login_required
@role_required(ROLE_INSTRUCTOR)
def quiz_grader(qid, course_id):
    '''
    This page allows to get all stats on a given quiz.
    '''
    stats = get_quiz_statistics(qid, course_id)
    accept_mime_type = request.accept_mimetypes.best
    query_mime_type = request.args.get("q", None)
    if accept_mime_type == "text/csv" or query_mime_type == "csv":
        columns = [ 'Last Name', 'First Name', 'Email', 'Initial Score', 'Max Initial Score', 'Revised Score', 'Max Revised Score', 
                    'Justification Score', 'Max Justification Score',
                    'Participation Score', 'Min Participation', 'Max Participation', 'Likes Given', 'Likes Received', 
                    'Designing Score', 
                    'Initial Score %', 'Revised Score %', 'Justifications %', 'Participation %', 'Designing %',
                    'Final Percentage' ]
        seqLen = lambda v: v if v is None else len(v)
        data = DataFrame([ [ s["last_name"], s["first_name"], s["email"], 
                s.get("initial_total_score", None), seqLen(s.get("initial_responses", None)), 
                s.get("revised_total_score", None), seqLen(s.get("revised_responses", None)), 
                s.get("justification_score", None), s.get("max_justification_score", None), 
                s.get("participation_score", None),
                s.get("min_participation_grade_threshold", None), s.get("participation_grade_threshold", None), 
                s.get("likes_given_count", None), s.get("likes_received_count", None), 
                s.get("designing_score", None), 
                s.get("initial_percent", None), s.get("revised_percent", None), s.get("justfication_percent", None), 
                s.get("participation_percent", None), s.get("designing_percent", None), s.get("total_percent", None) ] 
            for s in stats.students ],
            columns=columns, index=[student["id"] for student in stats.students])        
        headers = {}
        if request.args.get("d", "attachment") == "attachment":
            filename = (current_user.email + "-" + stats.quiz["title"]).replace(" ", "_")
            headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
        return Response(data.to_csv(index=False), mimetype="text/csv", headers=headers)
    if accept_mime_type == "application/json" or query_mime_type == "json":
        return jsonify(stats)

    numJustificationsOptions = list(range(1, 11))
    limitingFactorOptions = list(range(1, 100))
    quartileOptions = numJustificationsOptions

    return render_template('quiz-grader.html', current_user=current_user, 
                quiz = stats.quiz, course = stats.course, questions = stats.questions, distractors = stats.distractors, 
                students = stats.students, 
                # attempts = stats.attempts,
                # likes_given = stats.likes_given, likes_received = stats.likes_received, 
                limitingFactorOptions = limitingFactorOptions,
                # justification_like_count = stats.justification_like_count,
                numJustificationsOptions = numJustificationsOptions, quartileOptions = quartileOptions,
                course_id = course_id
                )

@pages.route('/quiz/<int:qid>/<int:course_id>/<int:student_id>/step3_grade', methods=['GET'])
@login_required
@role_required(ROLE_INSTRUCTOR)
def step3_grade(qid, course_id, student_id):
    q = models.Quiz.query.get_or_404(qid)
    course = models.Course.query.get_or_404(course_id)
    student = models.User.query.get_or_404(student_id)
    quiz_questions = q.quiz_questions

    quiz_question_ids = set(q.id for q in quiz_questions)
    quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(quiz_question_ids)).all()
    distractor_ids = [d.distractor_id for d in quiz_question_distractors]
    plain_distractors = models.Distractor.query.where(models.Distractor.id.in_(distractor_ids))
    distractor_per_question = {q_id: ds for q_id, ds in groupby(plain_distractors, key = lambda d: d.question_id)}    
    distractor_map = {d.id:d for d in plain_distractors}

    #unescaping part - left for backward compatibility for now
    
    attempt = models.QuizAttempt.query.filter_by(student_id=student.id, quiz_id=q.id, course_id=course.id).first()
    quiz_question_ids = [ int(qid) for qid in attempt.alternatives_map.keys() ]
    question_ids = [ qq.question_id for qq in quiz_questions ]
    # student created distractors where ids are in quiz_question_ids
    student_created_distractors = models.InvalidatedDistractor.query.where(models.InvalidatedDistractor.question_id.in_(question_ids), models.InvalidatedDistractor.author_id == current_user.id).all()
    student_created_distractors = {d.question_id:d for d in student_created_distractors}
    distractor_ids = [did for _, ds in attempt.alternatives_map.items() for did in ds]

    justifications = models.Justification.query.where(models.Justification.quiz_question_id.in_(quiz_question_ids), models.Justification.distractor_id.in_(distractor_ids), models.Justification.student_id == current_user.id).all()
    justification_map = {qid:{j.distractor_id:j for j in js} for qid, js in groupby(justifications, key=lambda x:x.quiz_question_id)}

    # we have all question_ids, using that we will find the all distractors for each question
    all_distractors = models.Distractor.query.where(models.Distractor.question_id.in_(question_ids)).all()

    question_model = [ { "id": qq.id, 
                        "alternatives": [ unescape(distractor_map[alternative].answer) if alternative in distractor_map else unescape(qq.question.answer) 
                                                for alternative in attempt.alternatives_map[str(qq.id)]
                                                if alternative in distractor_map or alternative == -1],
                        "choice": next((i for i, d in enumerate(attempt.alternatives_map[str(qq.id)]) if d == attempt.step_responses.get(str(qq.id), None)), -1), 
                        "invalidated_distractors": student_created_distractors,
                        "distractors_pool": [d for d in all_distractors if d.question_id == qq.question_id], 
                        "justifications": {a:js[did].justification for a, did in enumerate(attempt.alternatives_map[str(qq.id)]) if did in js},
                        **{attr:unescape(getattr(qq.question, attr)) for attr in [ "title", "stem", "answer" ]}}
                        for qq in quiz_questions
                        if str(qq.id) in attempt.alternatives_map
                        # for (qq, alternatives) in zip(quiz_questions, attempt.alternatives) 
                        for js in [justification_map.get(qq.id, {})]]

    quiz_model = { "id" : q.id, "title" : q.title, "description" : q.description, "deadline0": q.deadline0, "deadline1": q.deadline1, "deadline2": q.deadline2, "deadline3": q.deadline3, "deadline4": q.deadline4 } #we do not need any other fields from dump_as_dict

    # finding the reference justifications for each distractor
    explanations = {qid:{str(aid):{"justification": "Correct answer!" if did == -1 else unescape(distractor_map[did].justification), "is_correct": did == -1 } 
                        for aid, did in enumerate(alternatives) if did in distractor_map or did == -1}
                    for qid, alternatives in attempt.alternatives_map.items()}

    if q is None:
        flash('Quiz not found', 'danger')
        return redirect(url_for('pages.home'))
    
    if course is None:
        flash('Course not found', 'danger')
        return redirect(url_for('pages.home'))
    
    student_created_distractors = models.InvalidatedDistractor.query.where(models.InvalidatedDistractor.question_id.in_(question_ids), models.InvalidatedDistractor.author_id == student.id).all()
    
    return render_template('step3-grade.html', quiz = quiz_model, questions = question_model, course = course, student = student, explanations = explanations, student_created_distractors = student_created_distractors)

@pages.route('/quiz-copy/<int:qid>', methods=['GET'])
@login_required
@role_required(ROLE_INSTRUCTOR)
def quiz_copy(qid):
    '''
    This page allows to copy a quiz.
    '''
    quiz = models.Quiz.query.get_or_404(qid)
    evo_process = models.EvoProcess.query.filter_by(quiz_id=qid).first()
    if quiz is None:
        flash('Quiz not found', 'danger')
        return redirect(url_for('pages.home'))

    new_quiz = quiz.copy()
    models.DB.session.add(new_quiz)

    models.DB.session.commit()
    
    if evo_process is not None:
        new_evo_process = evo_process.copy(new_quiz.id)
        models.DB.session.add(new_evo_process)

    models.DB.session.commit()

    flash("Quiz copied successfully", "message")

    return redirect(url_for('pages.quizzes_browser'))

@pages.route('/courses/<int:cid>/student-list', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_INSTRUCTOR)
def student_list(cid):
    # print(f'In student_list, current_user: {current_user}, get_id: {current_user.get_id()}')
    course = models.Course.query.filter_by(id=cid).first()

    if course is None:
        flash('Course not found', 'danger')
        return redirect(url_for('pages.home'))

    instructor = models.User.query.get_or_404(current_user.get_id())
    if request.method == 'GET':
        return render_template('student-list.html', students=course.students)
    elif request.method == 'POST':
        # delete current student list if any so latest csv data is used
        models.DB.session.query(DB.Model.metadata.tables['CourseStudent']).filter(DB.Model.metadata.tables['CourseStudent'].c.CourseId == cid).delete()
        csvfile = request.files['csvfile']
        csvstring = csvfile.read().decode('utf-8')
        for email in [line.strip() for line in csvstring.splitlines()]:
            # print(email)
            # find student in DB
            student = models.User.query.filter_by(email=email).first()
            if student is None:  # student not in DB
                # add new User with empty password (needed as sentinel for when they login)
                student = models.User(email=email)
            student.courses.append(course)
            DB.session.add(student)
        DB.session.commit()
        return redirect(url_for('pages.student_list', cid=course.id))
