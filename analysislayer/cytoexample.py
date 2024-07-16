import sys

# RPW:  My example is based on the following payoff matrix.  
#       a "1" means that student got that quest correct, a "0"
#       means that they missed it.
# 
#          q1     q2     q3     q4
#     s1   1      1      1      0
#     s2   1      1      0      0
#     s3   1      1      0      0
#     s4   0      1      1      1
#     s5   0      0      1      1
#     s6   0      1      1      0
#     s7   0      1      1      0
#
# There are three distinct dimensions here.  There are also two students
# who scored exactly the same as someone else.  This might result in the 
# following extraction:
#
#                  s6
#                  ^ 
#                  |
#      s1 <- s2 <- * -> s5 -> s4
#                  
# And the equivalence classes:  {s2, s3} and {s6, s7}.
#
# Our DECA algorithm returns two structures.  The first is a list of lists,
# where each interior element is a tuple containg three things:
#    1. Test Result: the tuple of 1's and 0's corresponding to that student's row
#    2. Sum:  The sum of the 1's in the row (how many questions that student got right)
#    3. Student:  The unique identifier for the student (e.g., name) 
# 
# It also returns the equivalence classes in in the context dictionary.  The equivalence
# classes are a list 
#     

s1 = ( (1,1,1,0), 3, "s1" )
s2 = ( (1,1,0,0), 2, "s2" )
s3 = ( (1,1,0,0), 2, "s3" )
s4 = ( (0,1,1,1), 3, "s4" )
s5 = ( (0,0,1,1), 2, "s5" )
s6 = ( (0,1,1,0), 2, "s6" )
s7 = ( (0,1,1,0), 2, "s7" )

dims = [ [s2,s1], [s5,s4], [s6]]
eqClasses = { (1,1,0,0):set(["s2","s3"]),
              (0,1,1,0):set(["s6","s7"])}

# Just to make sure it worked as expected
for dim in dims:
    idx = 0
    sys.stdout.write("Dimenion " + str(idx) + ": ")
    for item in dim:
        result, resultSum, student = item
        sys.stdout.write(str(student) + " - ")
    sys.stdout.write('\n')
    idx += 1

print()
for result in eqClasses:
    print("Equivalent: ", eqClasses[result])
print()

# The following functions may also be helpful:
#    analysislayer/utils.py:   convertDecaQuestionDimsToCytoElementDict
#    analysislayer/plotter.py: GenerateDimensionGraph
