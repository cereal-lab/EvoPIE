# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from dataclasses import replace
from mimetypes import init
from operator import not_
from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from flask import Blueprint
from flask_login import login_required, current_user
from flask import flash
from sqlalchemy import not_
from sqlalchemy.sql import collate
from flask import Markup
from random import shuffle

import json, random, ast, re
import numpy as np
CLEANR = re.compile('<.*?>') 

from . import DB, models

import jinja2


pages = Blueprint('pages', __name__)

def checkToContinue(str1, index):

    if str1[index + 1] == ' ' and str1[index + 2] == '"' and str1[index - 1] == '"' and str1[index - 2].isdigit():
        return True
    return False

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
    # openColons = [m.start() for m in re.finditer(':', str)]
    # for i in range(len(openColons)):
    #     index = openColons[i]
    #     if checkToContinue(str1, index):
    #         j = index + 3
    #         while j < openColons[i + 1] - 7:
    #             if str1[j] == '"':
    #                 str1[j] = "'"
    # return ''.join(str1)

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
    #TODO #3 Refactor Markup(...).unescape()
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
    q.title = Markup(q.title).unescape()
    q.stem = Markup(q.stem).unescape()
    q.answer = Markup(q.answer).unescape()
    for d in q.distractors:
        d.answer = Markup(d.answer).unescape()
        d.justification = Markup(d.justification).unescape()
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
        # TODO #3 Refactor Markup(...).unescape()
        for d in qq.distractors:
            d.answer = Markup(d.answer).unescape()
            d.justification = Markup(d.justification).unescape()
            
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
    # TODO #3 unescaping so that the stem and answer are rendered in jinja2 template with | safe
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
    # TODO #3 unescaping so that the stem and answer are rendered in jinja2 template with | safe
    question.stem = Markup(question.stem).unescape()
    question.answer = Markup(question.answer).unescape()
    for d in question.distractors:
        d.answer = Markup(d.answer).unescape()
        d.justification = Markup(d.justification).unescape()
    

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
        qq.question.title = Markup(qq.question.title).unescape()
        qq.question.stem = Markup(qq.question.stem).unescape()
        qq.question.answer = Markup(qq.question.answer).unescape()
        # NOTE we do not have to worry about unescaping the distractors because the quiz-editor 
        # does not render them. However, if we had to do so, remember that we need to add to 
        # each QuizQuestion a field named alternatives that has the answer + distractors unescaped.
    if q.status != "HIDDEN":
        flash("Quiz not editable at this time", "error")
        #return redirect(url_for('pages.index'))
        return redirect(request.referrer)
    numJustificationsOptions = [num for num in range(1, 11)]
    limitingFactorOptions = [num for num in range(1, 100)]
    initialScoreFactorOptions = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    revisedScoreFactorOptions = initialScoreFactorOptions
    justificationsGradeOptions = initialScoreFactorOptions
    participationGradeOptions = initialScoreFactorOptions
    quartileOptions = numJustificationsOptions
    return render_template('quiz-editor.html', quiz = q.dump_as_dict(), limitingFactorOptions = limitingFactorOptions, initialScoreFactorOptions = initialScoreFactorOptions, revisedScoreFactorOptions = revisedScoreFactorOptions, justificationsGradeOptions = justificationsGradeOptions, participationGradeOptions = participationGradeOptions, numJustificationsOptions = numJustificationsOptions, quartileOptions = quartileOptions)
    




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

    # BUG we had to simplify the questions to avoid an escaping problem
    simplified_quiz_questions = [question.dump_as_simplified_dict() for question in q.quiz_questions]    
    # PBM - the alternatives for questions show unescaped when taking the quiz
    # SOL - need to unescape them before to pass them to the template
    
    ##for qq in quiz_questions:
    ##    for altern in qq["alternatives"]:
    ##        # experimenting, this works: tmp = jinja2.Markup(quiz_questions[0]["alternatives"][0][1]).unescape()
    ##        altern[1] = jinja2.Markup(altern[1]).unescape()
    ##        # nope... altern[1] = jinja2.Markup.escape(altern[1])
    # TODO #3 
    for qq in quiz_questions:
        qq.question.title = Markup(qq.question.title).unescape()
        qq.question.stem = Markup(qq.question.stem).unescape()
        qq.question.answer = Markup(qq.question.answer).unescape()
        for d in qq.distractors:
            d.answer = Markup(d.answer).unescape()
        # Preparing the list of alternatives for this question (these are the distractors + answer being displayed in the template)
        # This comes straight from models.py dump_as_dict for QuizQuestion
        tmp1 = [] # list of distractors IDs, -1 for right answer
        tmp2 = [] # list of alternatives, including the right answer
        tmp1.append(-1)
        tmp2.append(Markup(qq.answer).unescape())
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
        return redirect(request.referrer) #return redirect(url_for('pages.index'))

    if a and q.status == "STEP1":
        flash("You already submitted your answers for step 1 of this quiz. Wait for the instructor to open step 2 for everyone.", "error")
        return redirect(request.referrer) #return redirect(url_for('pages.index'))

    if not a and q.status == "STEP2":
        flash("You did not submit your answers for step 1 of this quiz. Because of that, you may not participate in step 2.", "error")
        return redirect(request.referrer) #return redirect(url_for('pages.index'))

    if a and q.status == "STEP2" and a[0].revised_responses != "{}":
        flash("You already submitted your answers for both step 1 and step 2. You are done with this quiz.", "error")
        return redirect(request.referrer) #return redirect(url_for('pages.index'))


    # finding the reference justifications for each distractor
    expl = { -1 : "This is the correct answer for this question"}
    for quiz_question in q.quiz_questions:
        for distractor in quiz_question.distractors:
            expl[distractor.id] = Markup(distractor.justification).unescape()
            
    # Handle different steps
    if a: # step == 2 or SOLUTIONS
        # retrieve the peers' justifications for each question
        quiz_justifications = {}
        count_distractor = 0
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
                count_distractor += 1
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
                number_to_select = min(q.num_justifications_shown , len(quiz_justifications[key_question][key_distractor]))
                #TODO FFS remove the above ugly, hardcoded, magic, number

                selected = []
                for n in range(number_to_select):                     
                    index = random.randint(0,len(quiz_justifications[key_question][key_distractor])-1)
                    neo = quiz_justifications[key_question][key_distractor].pop(index) #[index]
                    selected.append(neo)

                quiz_justifications[key_question][key_distractor] = selected

        if q.max_likes == -99:
            q.max_likes = number_to_select * (count_distractor + len(quiz_questions))
            models.DB.session.commit()

        initial_responses = [] 

        # FIXME TODO figure out how the JSON got messed up in the first place, then fix it instead of the ugly patch below
        asdict = json.loads(a[0].initial_responses.replace("'",'"'))
        for k in asdict:
            initial_responses.append(asdict[k])
        
        likes_given = len(LikesGiven(models.QuizAttempt.query.join(models.User)\
        .filter(models.QuizAttempt.quiz_id == qid)\
        .filter(models.QuizAttempt.student_id == u.id)\
        .order_by(collate(models.User.last_name, 'NOCASE'))\
        .first()))

        return render_template('student.html', explanations=expl, quiz=q, simplified_questions=simplified_quiz_questions, questions=quiz_questions, student=u, attempt=a[0], initial_responses=initial_responses, justifications=quiz_justifications, likes_given = likes_given)

    else: # step == 1

        return render_template('student.html', explanations=expl, quiz=q, simplified_questions=simplified_quiz_questions, questions=quiz_questions, student=u)




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


@login_required
def get_data(qid):
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

    questions = {}
    distractors = {}
    count_distractor = 0
    like_scores = {}
    grading_details = []
    likes_given = {}
    likes_received = {}
    count_likes_received = {}
    justification_grade = {}
    justificationLikesCount = {}
    quiz_questions = q.quiz_questions

    if len(grades) == 0:
        return q, grades, grading_details, distractors, questions, likes_given, likes_received, count_likes_received, like_scores, justification_grade

    # LikesGiven format: (Justification object, Likes4Justifcations object, quiz_id, quiz_question_id)
    # LikesReceived format: (Likes4Justification object, Justification object, quiz_id, quiz_question_id)
    for grade in grades:
        likes_given[grade.student_id] = LikesGiven(grade)
        likes_received[grade.student_id], count_likes_received[grade.student_id], justificationLikesCount[grade.student_id]  = LikesReceived(grade)

    for question in quiz_questions:
        with models.DB.session.no_autoflush:
            questions[str(question.id)] = models.Question.query.filter(question.question_id == models.Question.id).first()
        questions[str(question.id)].stem = Markup(questions[str(question.id)].stem).unescape()
        questions[str(question.id)].answer = Markup(questions[str(question.id)].answer).unescape()
        questions[str(question.id)].title = Markup(questions[str(question.id)].title).unescape()
        for distractor in question.distractors:
            if str(question.id) not in distractors:
                distractors[str(question.id)] = {}
            distractors[str(question.id)][str(distractor.id)] = Markup(distractor.answer).unescape()
            count_distractor += 1

    MaxLikes = q.max_likes
    LimitingFactor = q.limiting_factor
    for i in range(len(grades)):
        grading_details.append(QuizAttempt())
        grades[i].justifications = Markup(grades[i].justifications).unescape()
        grading_details[i].initial_responses = json.loads(grades[i].initial_responses.replace("'", '"'))
        grading_details[i].revised_responses = json.loads(grades[i].revised_responses.replace("'", '"'))
        # grading_details[i].justifications = json.loads(grades[i].justifications.replace("'", '"'))
        # print("The student is ", grades[i].student_id)
        # print(replaceModified(grades[i].justifications).replace('\\n', '\n').replace("\\'", "'"))
        # grading_details[i].justifications = json.loads(replaceModified(grades[i].justifications.replace('"', "'")).replace('\\n', '\n').replace("\\'", "'"))
        grading_details[i].justifications = ast.literal_eval(grades[i].justifications.replace("\\n", "a").replace('\\"', '\"'))
        # grading_details[i].justifications = ast.literal_eval(grades[i].justifications.replace('\\"', '\"').replace('\\n', '\n'))
        for j in range(len(grades)):
            if j != i:
                if grades[i].student_id not in like_scores:
                    like_scores[grades[i].student_id] = 0
                likes_by_g = len(LikesGiven(grades[j])) if len(LikesGiven(grades[j])) != 0 else 1
                like_scores[grades[i].student_id] += ( Likes(grades[j], grades[i]) * min( ( (MaxLikes * LimitingFactor) / likes_by_g ), 1 ) )
                # print (grades[i].student.email, Likes(grades[j], grades[i]), grades[j].student.email, likes_by_g, like_scores[grades[i].student_id])
    sorted_scores = list(like_scores.values())
    sorted_scores.sort()    
    if len(sorted_scores) > 0:
        median, median_indices = find_median(sorted_scores)
        Q1, Q1_indices = find_median(sorted_scores[:median_indices[0]])
        Q3, Q3_indices = find_median(sorted_scores[median_indices[-1] + 1:])

        quartiles = [Q1, median, Q3]
        for grade in grades:
            if q.status == "HIDDEN" or q.status == "STEP1":
                justification_grade[grade.student_id] = 0    
            else:
                justification_grade[grade.student_id] = decideGrades(q, like_scores[grade.student_id], quartiles)

        print(MaxLikes, sorted_scores, quartiles)
    return q, grades, grading_details, distractors, questions, likes_given, likes_received, count_likes_received, like_scores, justification_grade, justificationLikesCount

def getTotalScore(q, grades, justification_grade, likes_given):
    max_justfication_grade = max(q.first_quartile_grade, q.second_quartile_grade, q.third_quartile_grade, q.fourth_quartile_grade)
    max_score = round( ( len(q.quiz_questions) * q.initial_score_weight + len(q.quiz_questions) * q.revised_score_weight + max_justfication_grade * q.justification_grade_weight + 1 * q.participation_grade_weight), 2)
    total_scores = {}
    total_scores[-1] = max_score
    for grade in grades:
        likes_given_length = len(likes_given[grade.student.id]) if grade.student.id in likes_given else 0
        participation_grade = 1 if likes_given_length >= 0.8 * q.participation_grade_threshold and likes_given_length <= q.participation_grade_threshold else 0
        if (grade.student.id == 13):
            print("The participation grade is", participation_grade)
            print(justification_grade[grade.student.id])
        total_scores[grade.student.id] = round(grade.initial_total_score * q.initial_score_weight + grade.revised_total_score * q.revised_score_weight + justification_grade[grade.student.id] * q.justification_grade_weight + participation_grade * q.participation_grade_weight, 2)
    return total_scores


def decideGrades(quiz, score, ranges):
    grade = 0
    if score <= ranges[0]:
        grade = quiz.first_quartile_grade
    elif score > ranges[0]:
        if score <= ranges[1]:
            grade = quiz.second_quartile_grade
        elif score > ranges[1]:
            if score <= ranges[2]:
                grade = quiz.third_quartile_grade
            elif score > ranges[2]:
                grade = quiz.fourth_quartile_grade
    return grade


def find_median(sorted_list):
    indices = []

    list_size = len(sorted_list)
    median = 0

    if list_size % 2 == 0:
        indices.append(int(list_size / 2) - 1)  # -1 because index starts from 0
        indices.append(int(list_size / 2))

        median = (sorted_list[indices[0]] + sorted_list[indices[1]]) / 2
        pass
    else:
        indices.append(int(list_size / 2))

        median = sorted_list[indices[0]]
        pass

    return median, indices

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

def Likes(g, s):
    '''
    Gives us the amount of likes given by g to s for a quiz
    '''
    return len(models.DB.session.query(models.Likes4Justifications, models.Justification, DB.Model.metadata.tables['relation_questions_vs_quizzes'])\
        .filter(models.Justification.id == models.Likes4Justifications.justification_id)\
        .filter(models.Likes4Justifications.student_id == g.student_id)\
        .filter(models.Justification.student_id == s.student_id)\
        .filter(DB.Model.metadata.tables['relation_questions_vs_quizzes'].c.quiz_id == g.quiz_id)\
        .filter(DB.Model.metadata.tables['relation_questions_vs_quizzes'].c.quiz_question_id == models.Justification.quiz_question_id)\
        .all())


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

def LikesReceived(g):
    '''
    Likes received by student for a quiz
    '''
    actual_justifications = (models.DB.session.query(models.Likes4Justifications, models.Justification, DB.Model.metadata.tables['relation_questions_vs_quizzes'])\
        .filter(models.Justification.student_id == g.student_id)\
        .filter(models.Likes4Justifications.justification_id == models.Justification.id)\
        .filter(DB.Model.metadata.tables['relation_questions_vs_quizzes'].c.quiz_id == g.quiz_id)\
        .filter(DB.Model.metadata.tables['relation_questions_vs_quizzes'].c.quiz_question_id == models.Justification.quiz_question_id)\
        .group_by(models.Likes4Justifications.justification_id)\
        .all()
    )

    count_likes = (models.DB.session.query(models.Likes4Justifications, models.Justification, DB.Model.metadata.tables['relation_questions_vs_quizzes'])\
        .filter(models.Justification.student_id == g.student_id)\
        .filter(models.Likes4Justifications.justification_id == models.Justification.id)\
        .filter(DB.Model.metadata.tables['relation_questions_vs_quizzes'].c.quiz_id == g.quiz_id)\
        .filter(DB.Model.metadata.tables['relation_questions_vs_quizzes'].c.quiz_question_id == models.Justification.quiz_question_id)\
        .all()
    )

    justificationLikesCount = {}

    for data in count_likes:
        if data[1].justification not in justificationLikesCount:
            justificationLikesCount[data[1].justification] = 0
        justificationLikesCount[data[1].justification] += 1

    return actual_justifications, count_likes, justificationLikesCount

@pages.route('/grades/<int:qid>', methods=['GET'])
@login_required
def quiz_grader(qid):
    '''
    This page allows to get all stats on a given quiz.
    '''

    q, grades, grading_details, distractors, questions, likes_given, likes_received, count_likes_received, like_scores, justification_grade, justificationLikesCount = get_data(qid)

    numJustificationsOptions = [num for num in range(1, 11)]
    ''' 
    We are using the limitng factor to calculate the participation threshold, for example:

    Let's say The max likes is 36
    The default limiting factor is 0.5

    So the range of likes should be 14 - 18

    '''
    limitingFactorOptions = [num for num in range(1, 100)]
    initialScoreFactorOptions = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    revisedScoreFactorOptions = initialScoreFactorOptions
    justificationsGradeOptions = initialScoreFactorOptions
    participationGradeOptions = initialScoreFactorOptions
    quartileOptions = numJustificationsOptions

    LimitingFactor = q.limiting_factor

    total_scores = getTotalScore(q, grades, justification_grade, likes_given)
    

    return render_template('quiz-grader.html', quiz=q, all_grades=grades, grading_details = grading_details, distractors = distractors, questions = questions, likes_given = likes_given, likes_received = likes_received, count_likes_received = count_likes_received, like_scores = like_scores, justification_grade = justification_grade, limitingFactorOptions = limitingFactorOptions, initialScoreFactorOptions = initialScoreFactorOptions, revisedScoreFactorOptions = revisedScoreFactorOptions, justificationsGradeOptions = justificationsGradeOptions, participationGradeOptions = participationGradeOptions, LimitingFactor = LimitingFactor, total_scores = total_scores, justificationLikesCount = justificationLikesCount, numJustificationsOptions = numJustificationsOptions, quartileOptions = quartileOptions)

@pages.route("/getDataCSV/<int:qid>", methods=['GET'])
@login_required
def getDataCSV(qid):
    # resetTotalScores(qid)
    q, grades, grading_details, distractors, questions, likes_given, likes_received, count_likes_received, like_scores, justification_grade, justificationLikesCount = get_data(qid)
    total_scores = getTotalScore(q, grades, justification_grade, likes_given)
    csv = 'Last Name,First Name,Email,Initial Score,Revised Score,Grade for Justifications,Grade for Participation,Likes Given,Likes Received,Total Score,Final Percentage\n'
    for grade in grades:
        likes_given_length = len(likes_given[grade.student.id]) if grade.student.id in likes_given else 0
        likes_received_length = len(count_likes_received[grade.student.id]) if grade.student.id in likes_received else 0
        participation_grade = 1 if likes_given_length >=  0.8 * q.participation_grade_threshold and likes_given_length <= q.participation_grade_threshold else 0
        csv += grade.student.last_name + "," + grade.student.first_name + "," + grade.student.email + "," + str(grade.initial_total_score) + "," + str(grade.revised_total_score) + "," + str(justification_grade[grade.student.id]) + "," + str(participation_grade) + "," + str(likes_given_length) + "," + str(likes_received_length) + "," + str(total_scores[grade.student.id]) + " / " + str(total_scores[-1]) + "," + str( round(((total_scores[grade.student.id] / total_scores[-1] ) * 100), 1) ) + "%" + "\n"
    filename = (current_user.email + "-" + q.title).replace(" ", "_")
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename={}.csv".format(filename)})

@pages.route("/edit/LimitingFactor/<int:qid>", methods=['POST'])
@login_required
def changeLimitingFactor(qid):
    data = request.form.get('limitingFactorOptions')
        
    print(data)
    if data == "not applied":
        return redirect(url_for('pages.quiz_grader', qid = qid))
    q = models.Quiz.query.get_or_404(qid)
    q.limiting_factor = int(data) / 100
    models.DB.session.commit()
    return redirect(url_for('pages.quiz_grader', qid = qid))

@pages.route("/edit/InitialScoreFactor/<int:qid>", methods=['POST'])
@login_required
def changeInitialScoreFactor(qid):
    data = request.form.get('initialScoreFactorOptions')
        
    print(data)
    if data == "not applied":
        return redirect(url_for('pages.quiz_grader', qid = qid))
    q = models.Quiz.query.get_or_404(qid)
    # resetTotalScores(qid)
    q.initial_score_factor = int(data)
    models.DB.session.commit()
    return redirect(url_for('pages.quiz_grader', qid = qid))

@pages.route("/edit/RevisedScoreFactor/<int:qid>", methods=['POST'])
@login_required
def changeRevisedScoreFactor(qid):
    data = request.form.get('revisedScoreFactorOptions')
        
    print(data)
    if data == "not applied":
        return redirect(url_for('pages.quiz_grader', qid = qid))
    q = models.Quiz.query.get_or_404(qid)
    # resetTotalScores(qid)
    q.revised_score_factor = int(data)
    models.DB.session.commit()
    return redirect(url_for('pages.quiz_grader', qid = qid))

@pages.route("/edit/JustificationsGrade/<int:qid>", methods=['POST'])
@login_required
def changeJustificationsGrade(qid):
    data = request.form.get('justificationsGradeOptions')
        
    print(data)
    if data == "not applied":
        return redirect(url_for('pages.quiz_grader', qid = qid))
    q = models.Quiz.query.get_or_404(qid)
    # resetTotalScores(qid)
    q.justifications_grade = int(data)
    models.DB.session.commit()
    return redirect(url_for('pages.quiz_grader', qid = qid))

@pages.route("/edit/ParticipationGrade/<int:qid>", methods=['POST'])
@login_required
def changeParticipationGrade(qid):
    data = request.form.get('participationGradeOptions')
        
    print(data)
    if data == "not applied":
        return redirect(url_for('pages.quiz_grader', qid = qid))
    q = models.Quiz.query.get_or_404(qid)
    # resetTotalScores(qid)
    q.participation_grade = int(data)
    models.DB.session.commit()
    return redirect(url_for('pages.quiz_grader', qid = qid))

# def resetTotalScores(qid):
#     q = models.Quiz.query.get_or_404(qid)
#     attempts=models.QuizAttempt.query.join(models.User)\
#         .filter(models.QuizAttempt.quiz_id == qid)\
#         .filter(models.QuizAttempt.student_id == models.User.id)\
#         .order_by(collate(models.User.last_name, 'NOCASE'))\
#         .all()
#     for attempt in attempts:
#         attempt.initial_total_score = attempt.initial_total_score / q.initial_score_factor
#         attempt.revised_total_score = attempt.revised_total_score / q.revised_score_factor