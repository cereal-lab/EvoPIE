#each question - separate evolution
q1: d1 d2 ... dk_1 # 
q2: d1 d2 ... dk_2

q: d1 d2 .... dk #quality - how deceptive distractor is 

step1 * 
step2 

      q1
cs1:  d1d2d3 .. d__ 
cs1': d1d2d4 .. d__ 

[d1d2d3d4] -> present to student 

d1 d2 ... dk 
distractor itself is candidate solution 
DataFrame 
      s1    s2    s3     s4    ...    sn   
d1    nan
d2    nan
..
dk    nan 


# we have distribution policy for distractor - selection+mutation in evo process 
# 1. init - we pick 3 random distractors to coevaluate (random pick - more explorative)
      s1    s2    s3     s4    ...    sn   
d1    nan   nan   nan 
d2    0     0     0
..
d5    1     1     0
..
d7    0     0     0

HVC with weights on each step - 
..
dk    nan   nan 
# more exploitative approach 

exploration  <---> exploitation 
#Very exploitative to pick these 3 again 
#nondomination 
      s1    s2    s3     s4    ...    sn   
d1    nan   nan   nan 
d2    0     1     nan
..
d5    1     0     nan
..
d7    0     0     nan
# - we do not compare d2 and d5 again - because we know by Pareto they will be noncomparable. 


     s1    s2    s3     s4  ... sk  ...    sn   
d1    nan   nan   nan 
d2    0     1     nan
..
d5    1     0     nan
..
d7    0     0     nan


Final goal. We need quality metrics (for policy itself) for this (compare this): - why method A is better than method B
1. Instructor assignment of d 
2. Evo process - offline ? 
3. Reinforcement learning - TD algo Sutton Intro to RL (curse of dimensionality), Q learning 
4. Dummy algo: aggregation 
4. Comparison of different distractor distribution policy. Pareto vs difficulty. 
Criterias of the process sn - small enough, dk - could be big enough. We need to draw conclusions about d. 

1. s1 s2 s3 could be not enough - premature conclusion - conclusion could have weight - how we define this?
 - why the n distractors are better.
2. non-deterministic nature of response from student
3. Boltzman machine - use softmax distribution
4. Any signle objective (student) could turn dominance to non-dominance - post-analysis 

P-PHC
5. Pedagogy relevance of Pareto in selection - other quality - should student be objective?
   - problem with deception - we need other metric. Zone of approximate development. 
   - how to foster an improvement. More informative vs deception. Information gain. DECA, problem vs test
   - self-ethicasy - how we can measure it? Can we measure student boost of esteam? Other metric of distractors.
At least one distractor to ease student life (in the group) - important. Different cognitive load for random shuffling. 
Student guess vs common misconception.

What is good approximation for Pareto front? - The weight of the nonrepresented student is 0 (HVC with weights - check this) - so it is justifiable to work with only s1 .. s3 - we do not need to look for s4 ... sn.

Speed to find Pareto front - is good - no student lost of attention later. ??
Test results are aggregative - could be used for distractors. ??

Fairness question - students are not tested in same way. Other measure - fairness of test!!! Notion of difficulty of distractor.
Random distractors could be more difficult in one case than other.

--> which distractors student pick - Pareto front.

6. Innovization - distribution of distractors on Pareto to learn more about them (about students themselves - about objectives).




EvoParsons vs EvoPie 

1. Representation: [ p, d1, d2, .... dn ]

EvoParsons: program lib <- p, transform lib <- d1 ... dn 

EvoPie: [ d1d2d3, d, d3 ... dn  ] vs [ d1, d2, d2 ]
                                 | instructor sets 3 positions for quiz question ==> 3 distractors should be picked fro question
parent: [d1d2d3, d7d8d9 ...]     |  p  [ d1, d7, ... ]
child   [d1d2d4, d8d9d10, ...]   |  c1 [ d2, d9, ... ]
                                 |  c2 [ d3, d10, ... ]  --> c2 

[ d1d2d3d4, d7d8d9d10, ... ]     |  [ d1d2d3, d7d9d10  ]
  0 1 0 0   1 0 0 0                    
                                 | more pressure 

2. 


parent: [d1d2d3, d7d8d9 ...]  +1
child   [d1d2d4, d8d9d10, ...] +1



             p
p1           p1_id
  c1         p1_id
p2           p2_id
  c2         p2_id
  c3         p2_id
p3           p3_id
  c3         p3_id



                                   p
parent1: [d1d2d3, d7d8d9 ...]  -> id1 
child1: [d1d2d4, d7d10d11 ...] -> id1

parent2: [d1d2d4, d7d10d11 ...] -> id1



Strategies:

1. Use old evaluations to compare and require n more 
2. Use idea of GSEMO of dynamic population growth
3. Whom we want to preserve for == and non-domination



# Percent based vs weight basec knowledge base 

Question 1: 
    d_1  - 100%  --> [ d_1, d_2 ]  --> (100 + 50 + 25)
    d_2  - 50% 
    answer 
    d_3  - 25%

Question 1: 
    d_1  - 50%  --> [ d_2, d_3 ] --> random choice of these 
    d_2  - 25% 
    answer 
    d_3  - 10%    

TODO: 
1. quiz export - interaction matrix as DataFrame to csv and stdout - DONE
2. quiz run -n times - DONE
3. find bug with experimentation k 1 1 k 2 1 k 3 1 - DONE
Here expected values for interaction should all be 1 
1|37|[[1, 3, 7]]|{"86": 0, "87": 1, "88": 0, "89": 0}
1|41|[[2, 6, 9]]|{"100": 0, "101": 1}
4. Add weight for correct answer - check logic - DONE
5. Fix quiz attempt - preserve selected distractors on get_student Step1 and create attempt status column - DONE
6. Slider z-index fix - assign based on user interactions with handles - DONE


Experimentation 
1. Run n=30 times simple configs 2 distractors with 100% weight and check how frequently we have both of them in output