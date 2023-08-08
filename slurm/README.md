# Experiments with quiz-generation algorithms on simulated student knowledge

## Implementation

Quiz-generation algorithms could be found in files:

1. evopie/quiz_model.py - base interface for different algorithms. 
It contains QuizModel and QuizModelBuilder abstract classes, bases for all implementations. 

2. evopie/pphc_quiz_model.py - PPHC implementation of quiz search.
Parallel climbing towards the best quiz according to Pareto comparison.

3. evopie/sampling_quiz_model.py - sampling strategies implementation.
Resampling of distractor pools according to statistcs on interactions.

Simulated student knowledge generation in terms of multidimensional space is done in evopie/deca.py. 

## Experimentation 

Folder slurm contains script files used to collect experimental results.
Note, that evopie should be installed correctly before running the scripts.
Please consider repository wiki and root README for installation.

1. slurm/init_deca.sh will create multidimensional spaces for simulation 

2. Files rq-*.sh and exp.sh contains configuration for simulation runs. You can use them as template for your experimentation with new algorithms or to reproduce the results.

## Crude data 

Collected crude data is not currently published. TBD.
