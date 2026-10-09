# Reference

This document collects exact factual details about EvoPIE.

## Database schema

The following diagram shows the current EvoPIE database schema.

![EvoPIE database schema](assets/db-schema.png)

## Database entities

The schema includes these core tables:

- `user`: students, instructors, and admins.
- `course`: basic course information and course author.
- `CourseQuiz`: many-to-many relationship between courses and quizzes.
- `CourseStudent`: many-to-many relationship between courses and students.
- `quiz`: quiz information and attached configuration.
- `question`: question and answer pool.
- `distractor`: a plausible wrong answer and its reference justification.
- `quiz_question`: a question as used in a quiz.
- `relation_questions_vs_quizzes`: connects quizzes to quiz-question records.
- `quiz_questions_hub`: distractors attached to a quiz question.
- `quiz_attempt`: student answers for Step 1 and Step 2.
- `justification`: student-provided justifications for distractors.
- `attempt_justification`: justifications shown in an attempt.
- `likes4_justifications`: likes on justifications.
- `relation_questions_vs_attempts`: connects attempts to quiz-question records.
- `evo_process`: quiz model state.
- `glossary`: interaction post-processing data.
- `invalidated_distractor`: Step 3 distractors proposed by students.
- `student_knowledge`: student simulation data.
- `widgetstore`: cached dashboard graph objects and their context.

Courses, quizzes, and questions are independent entities connected through
relationship tables. A `quiz_question` represents a question as used in a quiz
and connects that usage to a subset of distractors through
`quiz_questions_hub`.

## SQLite inspection

Use `sqlite3` to inspect a concrete database file. Create a backup before
inspecting a production database.

```bash
sqlite3 DB_quizlib.sqlite
```

Useful SQLite shell commands include:

- `.tables`: list tables.
- `.schema [table]`: show table definitions.
- `.mode line`: show rows with property names.
- `.mode list`: show rows in compact format.
- `.help`: list SQLite shell commands.

## Roles

EvoPIE uses these role names:

- `STUDENT`
- `INSTRUCTOR`
- `ADMIN`

On an empty database, the first account created through the sign-up page
becomes an instructor account. Later accounts become student accounts.

## Quiz and attempt statuses

EvoPIE uses these quiz and quiz-attempt statuses:

- `HIDDEN`: the quiz is not available to students.
- `STEP1`: students answer individually and write justifications.
- `STEP2`: students review peer justifications and revise answers.
- `STEP3`: students may propose new distractors when Step 3 is enabled.
- `SOLUTIONS`: students may view solutions.

## Local commands

Initialize the database tables without dropping existing data:

```bash
uv run flask DB-init
```

Drop and recreate the database tables:

```bash
uv run flask DB-reboot
```

Populate sample quiz data:

```bash
uv run flask DB-populate
```

Run the dashboard updater once:

```bash
uv run python updater.py -1
```

Run the dashboard updater every 360 seconds:

```bash
uv run python updater.py 360
```

Open a Flask shell with EvoPIE loaded:

```bash
uv run flask shell
```

Then import the application objects:

```python
from evopie import *
```

## Environment variables

`FLASK_APP` selects the Flask application entry point. For local commands, use:

```bash
export FLASK_APP=evopie/__init__.py
```

`EVOPIE_DATABASE_URI` selects the database URI. If it is not set, EvoPIE uses a
local SQLite database. Docker Compose defaults it to
`sqlite:////app/data/db.sqlite`.

`EVOPIE_UPDATER_SLEEP` controls the updater delay when `updater.py` is run
without a command-line delay argument.

`EVOPIE_DATABASE_LOG` enables SQLAlchemy query logging to the configured file.

`EVOPIE_DEBUG=True` enables the debugpy listener used by the application.

The Docker Compose profiles also use these variables:

- `EVOPIE_DATA_DIR`: host data directory mounted at `/app/data`; defaults to
  `./data` for local mode and is required for production.
- `EVOPIE_SERVER_NAME`: nginx server name; required for production.
- `EVOPIE_CERT_DOMAIN`: certificate directory name under `live/`; defaults to
  `EVOPIE_SERVER_NAME`.
- `EVOPIE_CERTS_DIR`: host certificate directory mounted at
  `/etc/nginx/certs`; required for production.
- `EVOPIE_GIT_REF`: upstream branch, tag, or commit checked out by production
  image builds; defaults to `master`.

## Important paths

The local Docker profile defaults to `./data` on the host and mounts it at
`/app/data` in the containers. The default database file is
`/app/data/db.sqlite`.

The production profile mounts `EVOPIE_CERTS_DIR` at `/etc/nginx/certs`. Nginx
expects the certificate and key at:

```text
/etc/nginx/certs/live/${EVOPIE_CERT_DOMAIN}/fullchain.pem
/etc/nginx/certs/live/${EVOPIE_CERT_DOMAIN}/privkey.pem
```

## Grading components

EvoPIE can compute a total quiz grade from these components:

- Step 1 correctness grade.
- Step 2 revised correctness grade.
- Justification grade.
- Participation grade.
- Step 3 distractor-design grade, when Step 3 is enabled.

Step 1 and Step 2 correctness each award one point per correctly answered
question. Their component scores are the fraction of the step's questions
answered correctly.

The component weights are quiz parameters that instructors can configure.
EvoPIE converts available component scores to percentages and computes a
weighted average. If a component is unavailable for an attempt, the remaining
weights are rescaled to sum to one.

For student $s$, let $C_s$ be the grade components available for that attempt,
$g_c$ each component's score as a fraction from zero to one, and $w_c$ its
configured weight. The normalized weight is:

$$
\widetilde{w}_{c,s} =
\frac{w_c}{\sum_{d \in C_s} w_d}
$$

The total percentage is:

$$
G_s = 100 \cdot \sum_{c \in C_s} \widetilde{w}_{c,s} g_c
$$

## Participation grade

For a quiz with $Q$ questions, let $A_q$ be the number of alternatives for
question $q$. The total number of alternatives is:

$$
A = \sum_{q \in Q} A_q
$$

During Step 2, each alternative $a$ is shown with $J_a$ justifications. For a
student's attempt, the maximum number of likes available is the total number
shown:

$$
J = \sum_{a \in A} J_a
$$

The limiting factor $LF$ is an instructor-configured percentage representing
how many likes a student should give to receive full participation credit.

The stored participation threshold is rounded to an integer:

$$
PT = \mathrm{round}(LF \cdot J)
$$

The backend awards full participation credit when the number of likes is in
this range:

$$
\lfloor 0.8 \cdot PT \rfloor \leq \mathrm{likes\_given} \leq PT
$$

The Step 2 page displays a lower bound using rounding instead of flooring. For
some thresholds, the displayed lower bound can therefore differ from the
backend grading bound.

## Justification grade

For each student $s$, EvoPIE computes a justification score from likes received
from other students.

For each other student $k$, $\mathrm{Likes}(k, s)$ is the number of likes
that $k$ gave to $s$, and $\mathrm{Likes}(k)$ is the total number of likes
that $k$ gave in the quiz. The participation threshold used to normalize
student $k$'s likes is
$PT_k = LF \cdot J_k$, where $J_k$ is the number of justifications shown to
$k$. The implementation protects against division by zero by using a
denominator of at least one.

The student's justification score is:

$$
\mathrm{score}(s) =
\sum_{k \in S,\ k \neq s}
\mathrm{Likes}(k, s) \cdot
\min\left(\frac{PT_k}{\max(\mathrm{Likes}(k), 1)}, 1\right)
$$

EvoPIE compares student scores and assigns the configured point value for each
quartile. The first through fourth quartiles represent the lowest through
highest score groups. The implementation uses the first quartile, median, and
third quartile of the sorted scores as cutoffs; a score equal to a cutoff is
assigned to the higher group. If a cohort is too small to form a lower or upper
half, the implementation uses 0 or the median as that cutoff. Ties and small
cohorts can make the groups differ from exact 25% shares.

Defaults are 1 point for the first quartile, 3 for the second, 5 for the third,
and 10 for the fourth. Instructors can change these values per quiz. The
resulting points are normalized by the highest configured quartile value to
calculate the justification component percentage.

## Justification dispatching

Step 2 shows peer justifications grouped by question and answer choice. The
selection policy chooses a configured number of justification slots from each
group without replacement.

The policy has two goals:

- fairness: give each student a chance for their justifications to be seen;
- quality: show some justifications that are likely to be useful.

Implemented policy builders include:

- `j_random`: select a random justification.
- `j_least_seen`: prefer justifications shown fewer times.
- `j_not_seen`: prefer justifications not seen a configured number of times.
- `j_tournament`: select the best candidate from a random tournament.
- `j_e_greedy`: choose a fitness-best candidate with a configured probability;
  otherwise, apply a fallback policy.
- `j_softmax`: sample according to candidate fitness and a temperature value.
- `j_fitness_proportional`: select with probability proportional to fitness.
- `j_slot_group_till`: split slots into groups and apply sub-policies.

The current policy uses `j_least_seen` and `j_tournament`; the other builders
are implemented alternatives, not part of the current policy. It assigns about
60% of slots to least-seen selection, with
random tie-breaking. The remaining slots use tournament selection based on the
author's Step 1 score. Slot counts are rounded, with at least one slot assigned
to least-seen selection. Tournament size is about 10% of its candidate pool,
clamped between 1 and 7.

Selected justifications are stored in the student's `attempt_justification`
relationship and reused on subsequent page loads.

## Quiz models

The codebase contains these quiz model implementations:

- `RandomQuizModel`, which samples three distractors per question by default
  and reuses that selection;
- `PphcQuizModel`, which evolves candidate distractor combinations;
- `SamplingQuizModel`, which samples distractors using recorded interactions.

The default base model also supports returning instructor-selected distractors
without an adaptive model.

`SamplingQuizModel`'s `slot_based` strategy ranks candidate distractors using
configured features computed from student responses. These include how often a
distractor has been evaluated or selected, domination and nondomination
relationships between distractors, duplicate or overlapping response patterns,
and a response-based complexity score. The `strategy` and `hyperparams` values
in the model state control the strategy and feature priorities.

In `PphcQuizModel`, each candidate variant is a set of distractors. The model
creates child variants by changing distractor selections. For each student
response, it gives a candidate a point when the student's selected answer is
one of that candidate's distractors. It compares parent and child candidates
using their response-based evaluations and may replace a parent with a child.
After at least `pareto_n` student evaluations, it compares candidates across
those students using Pareto domination. It then mutates candidates for
subsequent evaluations. This evaluation rewards candidate distractors that
students have selected; it does not directly measure learning gains or
misconception discovery.

## Quiz model lifecycle

`get_quiz_builder().load_quiz_model(quiz)` restores the active model class and
its state from the quiz's `evo_process` record. If no active process exists,
the caller can request creation of a model.

When a student first enters Step 1, EvoPIE calls
`quiz_model.get_for_evaluation(student_id)` to get the distractors for that
attempt. After the student submits answers, EvoPIE calls
`quiz_model.evaluate(student_id, answers)`. Both operations save the updated
model-specific state in the `evo_process` table's `impl_state` field.

`set_quiz_model(model_class, settings)` configures the builder's model class
and settings; it is used by CLI experiments. The application package currently
calls `set_quiz_model(None)`, disabling model creation by default in the web
application.

The `EvoProcess` model uses a SQLAlchemy version column to detect conflicting
updates. The `retry_concurrent_update` decorator rolls back and reruns affected
requests after a stale-data error.

## Certificate operations

Docker Compose expects production certificates to exist on the host; it does
not obtain or renew them. Nginx reads the certificate and key from
`EVOPIE_CERTS_DIR`, under `live/EVOPIE_CERT_DOMAIN/`. A common source is
Let's Encrypt with certbot. For example, request a certificate for a public
server name with the standalone HTTP challenge:

```bash
sudo certbot certonly --standalone -d example.edu
```

This requires the domain to resolve to the server and port 80 to be available
for validation. On a host where certbot is installed, list its certificates
with:

```bash
sudo certbot certificates
```

Certificate renewal and any required nginx reload or container restart must be
configured outside Docker Compose. For local HTTPS testing, generate a
self-signed certificate with `scripts/create-local-certs.sh`.

## CLI experiment commands

EvoPIE defines Flask CLI commands for simulations and experiments. DECA
experiments use this command shape:

```bash
export EVOPIE_DATABASE_URI=sqlite:///$WORK/evopie/data/db.sqlite
export PYTHONPATH=$(uv run which python)
uv run flask quiz deca-experiments \
    --deca-spaces $WORK/evopie/data/deca-spaces \
    --algo-folder $WORK/evopie/data/algo \
    --results-folder $WORK/evopie/data/results \
    --random-seed 23 --num-runs 30 \
    --algo "$ALGO_JSON"
```

`ALGO_JSON` contains the selected quiz model class and its parameters, such as
`PphcQuizModel`, population size, Pareto settings, and gene size.

The `slurm` directory contains examples of shell scripts for running CLI
experiments with simulated student groups.

## Extending CLI commands

CLI groups and commands are defined in `evopie/cli.py`. The application
registers the `quiz`, `course`, `student`, and `deca` groups with Flask. Add a
command to the appropriate `AppGroup` using its Click command decorator.

The `quiz run` simulation uses Flask's test client to log in as simulated
students and submit requests to student routes. The `deca-experiment` commands
use Flask's test CLI runner to invoke other CLI commands as part of an
experiment. These commands support research simulations and data analysis;
they are not part of the normal student quiz workflow.

## Debugging

The repository includes VS Code launch configurations in
`.vscode/launch.json`. They run the `flask` module with `FLASK_APP=app.py` and
development settings. Examples include `CLI: DB init` and `CLI: quiz init`;
select a configuration in VS Code's Run and Debug view to start it with
breakpoint support. The corresponding Flask arguments are:

```text
DB-init
quiz init -nq 3 -nd 5
```

## REST routes

EvoPIE is a Flask application, not a complete standalone REST API. Some routes
return or accept JSON and support asynchronous pages, but the project does not
currently expose every operation needed for a separate single-page application.

These route groups are part of the REST foundation:

- `GET /questions`: list questions.
- `POST /questions`: create a question.
- `GET /questions/<id>`: read a question.
- `PUT /questions/<id>`: update a question's title, stem, and answer; it does
  not update its distractors.
- `DELETE /questions/<id>`: delete the question from the database; deletion is
  not a soft delete.
- `GET /questions/<id>/distractors`: list distractors for a question.
- `POST /questions/<id>/distractors`: create a distractor for a question.
- `GET /distractors/<id>`: read a distractor.
- `PUT /distractors/<id>`: update a distractor.
- `DELETE /distractors/<id>`: delete a distractor.
- `GET /quizquestions`: list quiz-question records.
- `POST /quizquestions`: create a quiz-question record.
- `GET /quizquestions/<id>`: read a quiz question.
- `PUT /quizquestions/<id>`: update a quiz question.
- `DELETE /quizquestions/<id>`: delete a quiz question.
- `POST /quizzes`: create a quiz.
- `GET /quizzes/<id>`: read a quiz.
- `PUT /quizzes/<id>`: update a quiz.
- `DELETE /quizzes/<id>`: delete a quiz.
- `GET /quizzes/<id>/take`: get quiz questions for the current step.
- `POST /quizzes/<id>/take`: submit answers for the current step.
- `GET /quizzes/<id>/responses`: read student responses for a quiz.
- `GET /quizzes/<id>/status`: read a quiz status.
- `POST /quizzes/<id>/status`: set a quiz status.
