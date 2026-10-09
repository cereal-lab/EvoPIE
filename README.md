# EvoPIE - Evolutionary Peer Instruction Environment

## What is EvoPIE?

EvoPIE is a web application that _"operationalizes"_ Peer Instruction (PI).

That is, it provides an environment (a web application) for conducting Peer
Instruction.

This is no ordinary environment, however, for EvoPIE allows PI to be conducted
in an _Evolutionary_ and _Asynchronous_ manner.

### Peer Instruction

Peer Instruction, canonically, is a method designed to teach Students in a
classroom in such a way that all Students end up meaningfully engaging in the
learning process.

It was popularized by Harvard professor Eric Mazur in the 90's. While its
precise form has evolved over time and across the literature, two defining
traits have remained consistent. In PI, Students first

1) apply whichever concepts lie at the core of the subject to learn, and then

2) they explain those concepts to other Students.

### _Asynchronous_ and _Evolutionary_

EvoPIE operationalizes PI by leveraging staged, multiple-choice quiz
activities. It gives Instructors the tools required create and evaluate these
assessments, and it gives Students the ability to complete them.

On a first pass, Students answer their newly assigned quizzes, picking
whichever choices they think are correct, but also simultaneously providing
justifications for all choices which they think are not.

Then, in a second phase, Students are allowed to take the same quizzes again.
This time, however, they are also provided with their peers' justifications
from the previous step, which they can optionally mark as "helpful." This gives
Students the opportunity to revise their previous answers based on an
interpretation of these justifications.

Before revealing a quiz's answers, Instructors can also have Students complete
an optional third step in which the latter group is tasked with composing
additional distractors (wrong choices).

EvoPIE records all of these interactions: choosing and revising answers,
writing justifications, reviewing and liking peers’ justifications, and
proposing distractors.

Since all of these interactions need not happen at the same time, we say that
EvoPIE provides an environment for conducting PI in an ***Asynchronous***
manner.

As Students complete a quiz, EvoPIE can generate variants of that quiz using a
variety of approaches. One such approach is called ***Evolutionary***: it
evolves a quiz toward variants whose distractors Students have been observed to
choose more often. This is achieved by a background evolutionary process that
models interactions with a quiz, followed by a sampling from that model to
generate variants.

## Acknowledgement

This material is based in part upon work supported by the National Science
Foundation under awards #2012967. Any opinions, findings, and conclusions or
recommendation expressed in this work are those of the authors and do not
necessarily reflect the views of the National Science Foundation.

## Documentation

EvoPIE's documentation is done via Markdown files located at `./docs`. Some of
them are:

- [`./docs/how-to-run.md`](docs/how-to-run.md): local setup and deployment steps.
- [`./docs/user-guide.md`](docs/user-guide.md): task-oriented instructions for
  Instructors, Students, and admins using EvoPIE through the web interface.
- [`./docs/troubleshooting.md`](docs/troubleshooting.md): FAQ-style fixes for
  common problems.
