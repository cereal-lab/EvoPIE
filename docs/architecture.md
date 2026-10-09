# Architecture

This document explains how EvoPIE works at a system level.

## EvoPIE in one sentence

EvoPIE is a web application for asynchronous peer instruction. Instructors
build multiple-choice quiz activities, students answer and revise those
activities in stages, and the system records the resulting answers,
justifications, likes, and grades for instruction and analysis.

## The learning flow

Peer Instruction is an active-learning approach: students apply course concepts
to questions and explain their thinking to peers. EvoPIE supports this exchange
asynchronously through staged quiz activities.

EvoPIE is organized around courses, questions, quizzes, and students.

An instructor creates questions. Each question has a correct answer and a set
of distractors, which are wrong but plausible answer choices. The instructor
then uses those questions to build quizzes and attaches quizzes to courses.

Students take a quiz through a staged workflow. The quiz's status is the
instructor-controlled stage available to the class; each student's attempt
status records that student's progress through the stages. EvoPIE creates an
attempt when a student first enters Step 1. A quiz may also require a
step-specific passphrase.

In Step 1, each student answers the quiz individually. For each answer choice
they do not select, students provide a justification explaining why that choice
seems incorrect.

In Step 2, students revisit the quiz after other students have completed Step
\ 1. They can see selected peer justifications for the alternatives and can
revise their answers. Students may also like useful peer justifications.

Step 3 is optional. When enabled, students can propose new distractors and
justify why those distractors are plausible wrong answers. Instructors can
later review and grade that work.

The Solutions stage lets students see the correct answers and instructor
justifications after the activity is complete.

## Roles

EvoPIE currently uses three main roles:

- students, who take quizzes and participate in peer instruction;
- instructors, who create and manage courses, questions, quizzes, and grades;
- admins, who can access administrative views.

On an empty database, the first account created through the sign-up page
becomes an instructor account. Later accounts become student accounts.

## Main application parts

The `evopie` package is the Flask web application. It defines the application,
routes, templates, quiz pages, instructor pages, authentication, and dashboard
registration.

The `datalayer` package contains database setup and model definitions. EvoPIE
stores users, courses, questions, distractors, quizzes, attempts,
justifications, likes, grading data, quiz model state, and dashboard data in
the database.

The `analysislayer` package supports dashboard and analysis features. It builds
derived views of quiz and student data that instructors can inspect through the
data dashboard.

The `updater.py` process refreshes analysis and dashboard data. In local
development it can be run once or in a loop. In Docker deployment it runs as a
separate service.

The `nginx` directory contains the production reverse-proxy configuration used
by the Docker Compose deployment.

## Database-centered state

EvoPIE persists quiz state in the database. This is important because web
requests are stateless: each page load or submission has to restore the current
state from stored records.

The database stores the structure of a quiz, the students attached to a course,
the answers students submitted, the justifications they wrote, the
justifications shown in Step 2, likes on justifications, and grading-related
values. The schema diagram is included in the
[reference](reference.md#database-schema).

Some operations are intentionally cached in the database. For example, once a
student receives a sampled quiz attempt or a sampled set of peer
justifications, that state is stored so refreshing the page does not create a
different activity for the same student.

## Quiz models

A quiz model is the part of EvoPIE that decides which distractors or quiz
variants should be used for students. The default behavior relies on instructor
selection, but EvoPIE also contains model implementations that can sample or
adapt quiz content based on collected interactions.

Quiz models receive student response outcomes and maintain their own
implementation-specific state. Depending on the selected model, those outcomes
can guide which distractors appear in later quiz variants. The project aims to
use interaction data to help instructors identify student misconceptions; the
models do not all represent this data as a probability distribution.

The current model choices include manual selection, random selection, Parallel
Pareto Hill Climbing, and sampling strategies based on interaction features.

## Justifications and peer instruction

Justifications are central to EvoPIE. In Step 1, students explain why
unselected alternatives are incorrect. In Step 2, other students can see
selected peer justifications while revising their answers.

EvoPIE stores these justifications and tracks which justifications were shown
to which student. Students can like useful justifications. Those likes
contribute to participation and justification-related grading.

When a student first enters Step 2, EvoPIE selects from justifications already
stored for the quiz. The current policy has two goals: give each student a fair
chance for their justifications to be seen, and show some justifications that
are likely to be useful. It combines least-seen selection for fairness with
quality-oriented selection for some remaining slots. The selected set is saved
on the student's quiz attempt and reused on later page loads.

Quiz-model state is also stored in the database, in the model-specific state
for that quiz's evolutionary process. SQLAlchemy version columns detect
conflicting concurrent updates. Affected web requests roll back and retry when
a stale update is detected.

## Grading and analytics

EvoPIE grades more than whether a final answer is correct. Depending on quiz
configuration, grades may include Step 1 performance, Step 2 performance,
justification quality, participation through likes, and optional Step 3
distractor-design work.

The data dashboard and grading pages help instructors inspect student
performance, peer-instruction activity, and derived analysis views.

## Deployment shape

EvoPIE can run directly with Pipenv, Flask, SQLite, and the updater process.
Docker Compose also provides a `local` profile that builds the web and updater
services from the current checkout and serves the app over HTTP without nginx.
Compose Watch can sync source changes into that local profile.

The `production` profile runs the web application and updater behind nginx,
which terminates HTTPS. It requires an explicit host data directory, server
name, and certificate directory; the deployment is not tied to a particular
domain. Production images are built from the upstream repository at the
configured `EVOPIE_GIT_REF`, rather than from the invoking local checkout. The
production profile can also be used with a self-signed certificate for local
HTTPS testing.
