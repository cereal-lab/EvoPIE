# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from dataclasses import replace
from datetime import datetime
import io
from math import exp
from mimetypes import init
from operator import not_
from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response, send_file
from flask import Blueprint
from flask_login import login_required, current_user
from flask import flash
from pandas import DataFrame
from sqlalchemy import not_
from sqlalchemy.sql import collate
from flask import Markup
import random
from evopie.evo import get_evo

from evopie.utils import role_required, retry_concurrent_update, find_median

from .config import QUIZ_ATTEMPT_SOLUTIONS, QUIZ_ATTEMPT_STEP1, QUIZ_ATTEMPT_STEP2, QUIZ_STEP1, QUIZ_STEP2, ROLE_INSTRUCTOR, ROLE_STUDENT, get_k_tournament_size, get_least_seen_slots_num
from .utils import unescape

import json, random, ast, re
import numpy as np

from . import DB, models

import jinja2

#used for justification histogram rendering
import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42


pages = Blueprint('pages', __name__)

def replaceModified(str):
    str1 = list(str)
    openTags = [m.start() for m in re.finditer('<p>', str)]
    closeTags = [m.start() for m in re.finditer('</p>', str)]
    singleQuotes = [m.start() for m in re.finditer('\'', str)]
    i = 0
    if len(openTags) == 0:
        return str.replace("'", '"')
    start = openTags[i]
    end = closeTags[i]
    for j in range(len(singleQuotes)):
        curr = singleQuotes[j]
        if curr > end:
            i += 1
            if i >= len(openTags):
                break
            start = openTags[i]
            end = closeTags[i]
        if not (curr > start and curr < end):
            str1[curr] = '\"'
    for j in range(closeTags[len(closeTags) - 1] + 4, len(str)):
        if str1[j] == "\'":
            str1[j] = "\""
    str = ''.join(str1)
    return str

class QuizAttempt:
    justifications = {}
    initial_responses = []
    revised_responses = []

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
    return render_template('quiz-editor.html', quiz = q.dump_as_dict(), limitingFactorOptions = limitingFactorOptions, initialScoreFactorOptions = initialScoreFactorOptions, revisedScoreFactorOptions = revisedScoreFactorOptions, justificationsGradeOptions = justificationsGradeOptions, participationGradeOptions = participationGradeOptions, numJustificationsOptions = numJustificationsOptions, quartileOptions = quartileOptions)


def get_possible_justifications(quiz):
    '''
    Collect all possible justifications from which policy should pick 
    :param quiz - quiz model
    '''
    justifications = {}
    for q in quiz.quiz_questions:
        justifications[str(q.id)] = {}
        for d in q.distractors:
            # get all justifications for that alternative / question pair
            res = models.Justification.query\
                .filter_by(quiz_question_id=q.id)\
                .filter_by(distractor_id=d.id)\
                .filter(not_(models.Justification.justification==""))\
                .filter(not_(models.Justification.justification=="<br>"))\
                .filter(not_(models.Justification.justification=="<p><br></p>"))\
                .filter(not_(models.Justification.justification=="<p></p>"))\
                .filter(not_(models.Justification.student_id==current_user.id))\
                .all()
            # justifications.extend(res)
            justifications[str(q.id)][str(d.id)] = res
        # also handle the solution -1
        res = models.Justification.query\
            .filter_by(quiz_question_id=q.id)\
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
        # quiz_justifications[str(q.id)] = question_justifications
        # justifications.extend(res)
        justifications[str(q.id)]["-1"] = res
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

@pages.route('/quiz/<int:quiz_id>/justification/histogram', methods=['GET'])
@login_required 
def get_justification_distribution(quiz_id):
    if not current_user.is_instructor():
        flash("You are not allowed to get justification distribution")
        return redirect(url_for('pages.index'))
    attempt_quality_attr = request.args.get("attempt_quality", "initial_total_score")   
    def attempt_quality(attempt):
        return getattr(attempt, attempt_quality_attr)    
    attempts = models.QuizAttempt.query.filter(models.QuizAttempt.quiz_id == quiz_id, models.QuizAttempt.status != QUIZ_ATTEMPT_STEP1).all() # assuming one per student for now 
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

@pages.route('/student/<int:qid>', methods=['GET'])
@login_required
@role_required(role=ROLE_STUDENT, redirect_route='pages.index', redirect_message="You are not allowed to take this quiz")
@retry_concurrent_update
def get_student(qid):
    '''
    Links using this route are meant to be sh
    ared with students so that they may take the quiz
    and engage in the asynchronous peer instrution aspects. 
    '''
    q = models.Quiz.query.get_or_404(qid)

    if q.status == "HIDDEN":
        flash("Quiz not accessible at this time", "error")
        return redirect(request.referrer) #return redirect(url_for('pages.index'))

    # TODO #3 we replace dump_as_dict with proper Markup(...).unescape of the objects'fields themselves
    # see lines commented out a ## for originals
    ##quiz_questions = [question.dump_as_dict() for question in q.quiz_questions]
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

    question_ids = set(q.id for q in quiz_questions)
    plain_distractors = models.Distractor.query.where(models.Distractor.question_id.in_(question_ids))
    distractor_per_question = {q_id: ds for q_id, ds in groupby(plain_distractors, key = lambda d: d.question_id)}    
    distractor_map = {d.id:d for d in plain_distractors}

    #unescaping part - left for backward compatibility for now
    def build_question_model(selected_distractor_ids):
        selected_distractors = [ [distractor_map[d_id] for d_id in question_distractor_ids if d_id in distractor_map] 
                                    for question_distractor_ids in selected_distractor_ids]
        questions_with_distractors = zip(quiz_questions, selected_distractors)
        return [ { "id": qq.id, 
                    "alternatives": sorted([(-1, unescape(qq.question.answer)), *[ (d.id, unescape(d.answer)) for d in distractors]], key=lambda x: random.random()),
                    **{attr:unescape(getattr(qq.question, attr)) for attr in [ "title", "stem", "answer" ]}}
                    for (qq, distractors) in questions_with_distractors ]
    
    # determine which step of the peer instruction the student is in
    a = models.QuizAttempt.query.filter_by(student_id=current_user.id).filter_by(quiz_id=qid).first()
    #we create QuizAttempt if not exist
    if (not a or a.status == QUIZ_ATTEMPT_STEP1) and (q.status != QUIZ_STEP1):
        flash("You did not submit your answers for step 1 of this quiz. Because of that, you may not participate in step 2.", "error")
        return redirect(request.referrer) #return redirect(url_for('pages.index'))
    elif a is None: #very first access
        evo = get_evo(q.id)
        if evo is None: #by default when no evo process - we pick all distractors selected by instructor
            selected_distractor_ids = [[d.id for d in distractor_per_question.get(qq.id, [])] for qq in quiz_questions]
        else: #rely on evo engine for selection of distractors
            selected_distractor_ids = evo.get_for_evaluation(current_user.id)        
            selected_distractor_ids = [list(ds) for ds in selected_distractor_ids]
        a = models.QuizAttempt(quiz_id=qid, student_id=current_user.id, status = QUIZ_ATTEMPT_STEP1, selected_distractors=json.dumps(selected_distractor_ids))
        models.DB.session.add(a)
        models.DB.session.commit()
        question_model = build_question_model(selected_distractor_ids)
        if request.accept_mimetypes.accept_html:            
            return render_template('student.html', quiz=q.dump_as_dict(), questions=question_model, student=current_user)
        return jsonify({"questions":question_model})
    elif a.status == QUIZ_ATTEMPT_STEP1:
        #load existing in db distractors 
        selected_distractor_ids = json.loads(a.selected_distractors)
        question_model = build_question_model(selected_distractor_ids)
        if request.accept_mimetypes.accept_html:            
            return render_template('student.html', quiz=q.dump_as_dict(), questions=question_model, student=current_user)
        return jsonify({"questions":question_model})
    elif a.status == QUIZ_ATTEMPT_STEP2 and q.status == QUIZ_STEP1:
        flash("You already submitted your answers for step 1 of this quiz. Wait for the instructor to open step 2 for everyone.", "error")
        return redirect(request.referrer) #return redirect(url_for('pages.index'))
    elif a.status == QUIZ_ATTEMPT_STEP1 and q.status == QUIZ_STEP2:
        flash("You did not submit your answers for step 1 of this quiz. Because of that, you may not participate in step 2.", "error")
        return redirect(request.referrer) #return redirect(url_for('pages.index'))
    elif a.status == QUIZ_ATTEMPT_SOLUTIONS and q.status == QUIZ_STEP2 and a.revised_responses != "{}":
        flash("You already submitted your answers for both step 1 and step 2. You are done with this quiz.", "error")
        return redirect(request.referrer) #return redirect(url_for('pages.index'))            
    elif a.status == QUIZ_ATTEMPT_STEP2 or a.status == QUIZ_ATTEMPT_SOLUTIONS:
        if a.selected_justifications_timestamp is None: #attempt justifications were not initialized yet
            # retrieve the peers' justifications for each question  
            possible_justifications = get_possible_justifications(q)

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
            attempts = models.QuizAttempt.query.filter_by(quiz_id = qid).where(models.QuizAttempt.student_id.in_(student_ids), models.QuizAttempt.status != QUIZ_ATTEMPT_STEP1).all()
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

            a.selected_justifications.extend(j for d in selected_justification_map.values() for js in d.values() for j in js)

            a.max_likes = sum(len(js) for d in selected_justification_map.values() for js in d.values())
            a.participation_grade_threshold = round(a.max_likes * q.limiting_factor)
            #Idea: put another select to check if we have someting for this attempt id 
            a.selected_justifications_timestamp = datetime.now()
            models.DB.session.commit()
        else: 
            #justification list to map
            # selected_justification_map = {}
            selected_justifications = a.selected_justifications #here db query for selected justififcations
            quiz_question_ids = set(str(j.quiz_question_id) for j in selected_justifications)
            distractor_ids = set(str(j.distractor_id) for j in selected_justifications)
            selected_justification_map = {qid:{did:[] for did in distractor_ids} for qid in quiz_question_ids}
            for j in selected_justifications:
                selected_justification_map[str(j.quiz_question_id)][str(j.distractor_id)].append(j)
        initial_responses = [] 

        # FIXME TODO figure out how the JSON got messed up in the first place, then fix it instead of the ugly patch below
        asdict = json.loads(a.initial_responses.replace("'",'"'))
        for k in asdict:
            initial_responses.append(asdict[k])
        
        likes_given = len(LikesGiven(models.QuizAttempt.query.join(models.User)\
        .filter(models.QuizAttempt.quiz_id == qid)\
        .filter(models.QuizAttempt.student_id == current_user.id, models.QuizAttempt.status != QUIZ_ATTEMPT_STEP1)\
        .order_by(collate(models.User.last_name, 'NOCASE'))\
        .first()))

        #TODO: questions_with_distractors should be taken from QuizAttempt 
        selected_distractor_ids = json.loads(a.selected_distractors)
        question_model = build_question_model(selected_distractor_ids)

        # finding the reference justifications for each distractor
        expl = { -1: "This is the correct answer for this question",
                **{did.id:unescape(distractor_map[did].justification) if did in distractor_map else ''
                        for dids in selected_distractor_ids
                        for did in dids }}

        # quiz_questions = q.dump_as_dict()['quiz_questions']
        return render_template('student.html', explanations=expl, quiz=q.dump_as_dict(),
            questions=question_model, student=current_user, attempt=a.dump_as_dict(), initial_responses=initial_responses, 
            justifications=selected_justification_map, likes_given = likes_given)


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

from dataclasses import dataclass
from .utils import groupby

#NOTE: no model data should be present on UI
@dataclass
class QuizStats:
    quiz: dict # 1 level dict: props, one quiz with name-value props
    questions: dict # 2 level dict: question_id: props. key question_id and value is another dict 
    distractors: dict # 3 level dict: question_id:distractor_id:props
    students: list # list of quiz students: list of props
    # attempts: dict # 2 level student_id: props
    # likes_given: dict # 1 level: student_id: list of justification props
    # likes_received: dict # 1 level - similar to prev
    # justification_like_count: dict #3 level: question_id:distractor_id:justification_text:count
    # justification_scores: dict #dict student id: score 
    # total_score: dict #dict student id: score 
    # max_total_score: dict #dict student id: score 

def get_quiz_statistics(qid):
    '''
    This page allows to get all stats on a given quiz.
    '''    
    quiz = models.Quiz.query.get_or_404(qid)

    quiz_questions = quiz.quiz_questions
    question_ids = set(qu.question_id for qu in quiz_questions)
    plain_questions = models.Question.query.where(models.Question.id.in_(question_ids)).all()
    questions = {q.id:{**q.dump_as_simplified_dict(), **{attr:unescape(getattr(q, attr)) 
                                                            for attr in ["stem", "answer", "title"]} } 
                    for q in plain_questions}

    plain_distractors = models.Distractor.query.where(models.Distractor.question_id.in_(question_ids)).all()
    distractors = { qid : {d.id : unescape(d.answer) for d in ds} 
                    for (qid, ds) in groupby(plain_distractors, key = lambda d: d.question_id) } 

    plain_attempts = models.QuizAttempt.query.where(models.QuizAttempt.quiz_id == qid, models.QuizAttempt.status != QUIZ_ATTEMPT_STEP1).all()

    stats = QuizStats(quiz.dump_as_dict(), questions, distractors, students = [])

    if len(plain_attempts) == 0:
        return stats  
    attempts_map = {a.student_id: a for a in plain_attempts} #assume 1 attempt for 1 student - otherwise use other grouping
        
    student_ids = attempts_map.keys()        
    plain_justifications = models.Justification.query.where(models.Justification.student_id.in_(student_ids)).all()
    justification_map = {j.id:j.dump_as_dict() for j in plain_justifications}

    plain_likes = models.Likes4Justifications.query.where(models.Likes4Justifications.student_id.in_(student_ids)).all()
    likes_given = { **{ a.student_id: [] for a in plain_attempts if a.revised_scores != ''  },
                    **{ student_id: [justification_map[l.justification_id] for l in student_likes if l.justification_id in justification_map] 
                        for student_id, student_likes in groupby(plain_likes, key = lambda like: like.student_id) }}
    
    like_scores = { a.student_id: sum(parts)
        for a in plain_attempts 
        for parts in [[justifications_liked_by_o_to_a * min(participation_threshold_of_o / max(len(given_likes_by_o), 1), 1) 
                for o in plain_attempts if a.student_id != o.student_id and o.student_id in likes_given
                for given_likes_by_o in [likes_given.get(o.student_id, [])]
                for participation_threshold_of_o in [ quiz.limiting_factor * o.max_likes ]
                for justifications_liked_by_o_to_a in [sum(1 for j in given_likes_by_o if j["student_id"] == a.student_id)]]]
        if len(parts) > 0 or a.revised_scores != ''}            
        
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
    likes_received = {**{ a.student_id: [] for a in plain_attempts if a.revised_scores != ''  },
                        **{student_id: list(js) for student_id, js in groupby(student_justifications, key=lambda j: j["student_id"])}}
    
    justification_like_count = {student_id:{j["justification"]:j["num_likes"] for j in student_js} for student_id, student_js in likes_received.items()}

    #compute total scores 
    max_justfication_grade = max(quiz.first_quartile_grade, quiz.second_quartile_grade, quiz.third_quartile_grade, quiz.fourth_quartile_grade)
    num_questions = len(quiz_questions)
    total_scores = {}
    max_total_scores = {}
    participation_scores= {}
    for attempt in plain_attempts:    
        sid = attempt.student_id
        grade_parts = []
        if attempt.initial_scores != '':
            grade_parts.append((attempt.initial_total_score, num_questions, quiz.initial_score_weight))
        if attempt.revised_scores != '': #at step2 when revised scores are known
            grade_parts.append((attempt.revised_total_score, num_questions, quiz.revised_score_weight))
        if sid in justification_scores:
            grade_parts.append((justification_scores[sid], max_justfication_grade, quiz.justification_grade_weight))
        if sid in likes_given:
            likes_given_length = len(likes_given[sid])
            participation_scores[sid] = 1 if likes_given_length >= round(attempt.get_min_participation_grade_threshold()) and likes_given_length <= attempt.participation_grade_threshold else 0
            grade_parts.append((participation_scores[sid], 1, quiz.participation_grade_weight))   
        attempt_grades, max_grades, weights = tuple(zip(*grade_parts)) #unzip 
        # weights should sum up to 100 - so in case when some of grades are not available - we rescale 
        total_weights = sum(weights) 
        weights = [ w / total_weights for w in weights ]
        total_scores[sid] = sum(w * g for w, g in zip(weights, attempt_grades))
        max_total_scores[sid] = sum(w * g for w, g in zip(weights, max_grades))
    
    plain_students = models.User.query.where(models.User.id.in_(student_ids)).order_by(collate(models.User.last_name, 'NOCASE')).all()
    stats.students = [{**a.dump_as_dict(), **s.dump_as_dict(), 
                        "likes_given": likes_given.get(s.id, None),
                        "likes_given_count": len(likes_given[s.id]) if s.id in likes_given else None,
                        "like_score": like_scores.get(s.id, None),
                        "initial_total_score": a.initial_total_score if a.initial_scores != '' else None,
                        "revised_total_score": a.revised_total_score if a.revised_scores != '' else None,
                        "justification_score": justification_scores.get(s.id, None),
                        "likes_received": likes_received.get(s.id, None),
                        "likes_received_count": sum(j["num_likes"] for j in likes_received[s.id]) if s.id in likes_received else None,
                        "justification_like_count": justification_like_count.get(s.id, {}),
                        "min_participation_grade_threshold": int(a.get_min_participation_grade_threshold()) if a.revised_scores != '' else None,
                        "participation_grade_threshold": int(a.participation_grade_threshold) if a.revised_scores != '' else None,
                        "participation_score": int(participation_scores[s.id]) if s.id in participation_scores else None,
                        "total_score": student_score,
                        "max_total_score": max_student_score,
                        "initial_responses": {int(k):v for k, v in json.loads(a.initial_responses.replace("'", '"')).items()},
                        "revised_responses": {int(k):v for k, v in json.loads(a.revised_responses.replace("'", '"')).items()},
                        "justifications": ast.literal_eval(unescape(a.justifications).replace("\\n", "a").replace('\\"', '\"')),
                        "total_percent": (None if student_score is None or max_student_score is None else round(student_score * 100 / max_student_score, 1))}
                        for s in plain_students 
                        if s.id in attempts_map 
                        for a, student_score, max_student_score in [(attempts_map[s.id], 
                            round(total_scores[s.id], 2) if s.id in total_scores else None,
                            round(max_total_scores[s.id], 2) if s.id in max_total_scores else None)]]

    return stats

def getNumJustificationsShown(qid):
    q = models.Quiz.query.get_or_404(qid)
    # retrieve the peers' justifications for each question
    number_to_select = 0
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
            number_to_select = min(q.num_justifications_shown, len(quiz_justifications[key_question][key_distractor]))
            #TODO FFS remove the above ugly, hardcoded, magic, number

            selected = []
            for n in range(number_to_select):                     
                index = random.randint(0,len(quiz_justifications[key_question][key_distractor])-1)
                neo = quiz_justifications[key_question][key_distractor].pop(index) #[index]
                selected.append(neo)

            quiz_justifications[key_question][key_distractor] = selected
    
    return number_to_select

def LikesGiven(g):
    '''
    All likes given by g for a particular quiz
    '''
    return (models.DB.session.query(models.Justification, models.Likes4Justifications, DB.Model.metadata.tables['relation_questions_vs_quizzes'])
        .filter(models.Likes4Justifications.student_id == g.student_id)\
        .filter(models.Likes4Justifications.justification_id == models.Justification.id)\
        .filter(DB.Model.metadata.tables['relation_questions_vs_quizzes'].c.quiz_id == g.quiz_id)\
        .filter(DB.Model.metadata.tables['relation_questions_vs_quizzes'].c.quiz_question_id == models.Justification.quiz_question_id)\
        .all())

@pages.route('/grades/<int:qid>', methods=['GET'])
@login_required
@role_required(ROLE_INSTRUCTOR)
def quiz_grader(qid):
    '''
    This page allows to get all stats on a given quiz.
    '''
    stats = get_quiz_statistics(qid)
    accept_mime_type = request.accept_mimetypes.best
    query_mime_type = request.args.get("q", None)
    if accept_mime_type == "text/csv" or query_mime_type == "csv":
        columns = [ 'Last Name', 'First Name', 'Email', 'Initial Score', 'Revised Score', 'Grade for Justifications',
                    'Min Participation','Likes Given', 'Max Participation', 'Grade for Participation', 'Likes Received',
                    'Total Score', 'Max Possible Score', 'Final Percentage' ]
        data = DataFrame([ [ s["last_name"], s["first_name"], s["email"], 
                s.get("initial_total_score", None), s.get("revised_total_score", None), 
                s.get("justification_score", None), s.get("min_participation_grade_threshold", None), 
                s.get("likes_given_count", None), s.get("participation_grade_threshold", None), s.get("participation_score", None),
                s.get("likes_received_count", None), s.get("total_score", None), s.get("max_total_score", None), 
                s.get("total_percent", None) ] 
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
                quiz = stats.quiz, questions = stats.questions, distractors = stats.distractors, 
                students = stats.students, 
                # attempts = stats.attempts,
                # likes_given = stats.likes_given, likes_received = stats.likes_received, 
                limitingFactorOptions = limitingFactorOptions,
                # justification_like_count = stats.justification_like_count,
                numJustificationsOptions = numJustificationsOptions, quartileOptions = quartileOptions,
                # justification_grade = stats.justification_scores, total_scores = stats.total_scores, 
                # max_total_scores = stats.max_total_scores
                )
