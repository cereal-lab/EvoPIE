import sys
import numpy as np

import analysislayer.utils as dataUtils
import pandas as pd

from datalayer import LOGGER

def cleanupForStudentAnalysis(results, questionSubset=[], scoreThreshold=1.0):
  """
  Filter the data for doing student-based analysis:
    * Strip out students for whom there's no response on
      the specified questions;
    * Set the 'testResult' to True for each question that
      the student got entirely correct;
    * Organize as a list of tuples, where each tuple is a student and
      the tuple is the vector of results of how that student performed
      on each question;
    * Throw out duplicates of specific result configurations.
  """
  # Use only students that have taken the specified questions
  students = []
  studentEquivalenceClassSize = {}
  
  intersectedQuestions = set()
  
  for student in results:
    studentQuestionSet = set(results[student])
    if questionSubset.issubset(set(results[student])):
      students.append(student)
      if len(intersectedQuestions) == 0:
        intersectedQuestions = studentQuestionSet
      else:
        intersectedQuestions = intersectedQuestions.intersection(studentQuestionSet)
    
  students.sort()
  questions = list(intersectedQuestions)
  questions.sort()

  studentEquivalenceClass = {}

  # For each question and student, give a 'True' if the student
  # got *all* instances of that question correct and 'False' otherwise.
  testDict = {}
  for student in students:
    resultList = []
    for question in questions:
      resultList.append(results[student][question]['score'] >= scoreThreshold)
    testResult = tuple(resultList)

    # Ensures only one copy of tests with a specific result configuration
    # is retained (i.e., reserves uniqueness of result)
    testDict[testResult] =  (testResult, sum(testResult), student)
    if testResult in studentEquivalenceClassSize:
      studentEquivalenceClass[testResult].append(student)
    else:
      studentEquivalenceClass[testResult] = [student]

    # Each entry in that dictionary is a tuple corresponding to a specific student.
    # * The first field of that tuple is a vector of Booleans, where True values
    #   appear only when the student "passes" a question.
    # * The second field is total number of successful questions
    # * The third field is the student ID
    # * The fourth field is a dictionary of student equivalencies

  return testDict.values(), intersectedQuestions, set(students), studentEquivalenceClass


def cleanupForQuestionAnalysis(results, questionSubset=set(), scoreThreshold=1.0):
  """
  Filter the data for doing question-based analysis:
    * Strip out students for whom there's no response on
      the specified questions;
    * Set the 'testResult' to True for each question that
      the student got at least one wrong;
    * Organize as a list of tuples, where each tuple is a question and
      the tuple is the vector of results of what students solved
      that question correctly;
    * Throw out duplicates of specific result configurations.
  """
  # Use only students that have taken the specified Questions
  students = []
  intersectedQuestions = set()
  for student in results:
    studentQuestionSet = set(results[student].keys())
    if questionSubset.issubset(studentQuestionSet):
      students.append(student)
      if len(intersectedQuestions) == 0:
        intersectedQuestions = studentQuestionSet
      else:
        intersectedQuestions = intersectedQuestions.intersection(studentQuestionSet)

  students.sort()
  questions = list(intersectedQuestions)
  questions.sort()

  questionEquivalencyClass = {}

  # For each question and student, give a 'True' if the student
  # got *all* instances of that question correct and 'False' otherwise.
  testDict = {}
  for question in questions:
    resultList = []
    for student in students:
      # Paul, did you mean to include when correct < total or should this have been correct >= total?
      # Amruth, For Question analysis, a 'win' for the Question is when the student gets at least one wrong
      resultList.append( results[student][question]['score'] < scoreThreshold )
    testResult = tuple(resultList)

    # Ensures only one copy of tests with a specific result configuration
    # is retained (i.e., preserves uniqueness of result)
    testDict[testResult] =  (testResult, sum(testResult), question)

    # Builds the equivalency classes for tests that have identical result vectors
    if testResult in questionEquivalencyClass:
      questionEquivalencyClass[testResult].append(question)
    else:
      questionEquivalencyClass[testResult] = [question]

    # Each entry in that dictionary is a tuple corresponding to a specific Question/template.
    # * The first field of that tuple is a vector of Booleans, where True values
    #   appear only when the test "fails" a student.
    # * The second field is total number of failed students
    # * The third field is the template or Question ID
    # * The fourth field is a dictionary of question equivalencies
      
  return testDict.values(), intersectedQuestions, set(students), questionEquivalencyClass

  
def tupleAnd(t1,t2):
  """
  A simple wrapper function that compares two tuples using logical And.
  It assumes the tuples are the same dimensionality and contain Booleans.
  """
  return tuple(map(lambda a,b: a and b,  t1,  t2))

def tempPrint(a,b,c):
  for idx in range(len(a[0])):
    if a[0][idx]:
      sys.stdout.write('1')
    else:
      sys.stdout.write('0')
  LOGGER.info('')

  for idx in range(len(b[0])):
    if b[0][idx]:
      sys.stdout.write('1')
    else:
      sys.stdout.write('0')
  LOGGER.info('')

  for idx in range(len(c[0])):
    if c[0][idx]:
      sys.stdout.write('1')
    else:
      sys.stdout.write('0')
  LOGGER.info('')

  d = tupleAnd(a[0],b[0])
  for idx in range(len(d)):
    if d[idx]:
      sys.stdout.write('1')
    else:
      sys.stdout.write('0')
  LOGGER.info('')

  LOGGER.info(a[0])
  LOGGER.info(b[0])
  LOGGER.info(c[0])
  LOGGER.info(d)
  
  LOGGER.info('')
  

def filterTests(tests, omitSpanned=True, quiet=False):
  """
  This function sorts and filters the data to ensure no unnecessary redundancies
  in configuration of results and also sorts them in order of the number of
  successful tests.
  """
  tests = sorted(tests, key=lambda x: x[1])
  tests.reverse()

  spanned = set()

  if omitSpanned:
    for idx in range(len(tests)):
      for jdx in range(len(tests)):
        for kdx in range(len(tests)):
          indexSet = set([tests[idx][2], tests[jdx][2], tests[kdx][2]])
          if (len(indexSet) == 3) and (len(indexSet.intersection(spanned)) == 0):
            t1 = tests[idx][0]
            t2 = tests[jdx][0]
            t3 = tests[kdx][0]
            if (t3 == tupleAnd(t1,t2)):
              spanned.add(tests[kdx][2])
            
  keeping = []
  for test in tests:
    if (not test[2] in spanned):
      keeping.append(test)

  if not quiet:
    LOGGER.info("Spanned set: ", spanned)

  return keeping


def mooCompare(v1, v2):
  """
  Compare two vectors in a multiobjective sense.  This routine returns two values.
  The first indicates whether or not the two vectors can be compared in terms of
  total ordering.  The second returns the result of the comparison, assuming they
  can be compared.  If the two vectors are equal, it returns True and 0.  If the
  first vector Pareto dominates the second, return True and 1.  If the second
  Pareto dominates the first, return True and -1.  Otherwise it returns False and
  0, though the zero value is meaningless in this case.
  """
  a = np.array(v1)
  b = np.array(v2)  
  
  if all(a==b):
    return True, 0
  elif all(a >= b) and any(a > b):
    return True, 1
  elif all(b >= a) and any(b > a):
    return True, -1
  else:
    return False, 0
  
  
    
def extractDimensions(filteredTests):
  """
  Construct the geometric dimensions of interaction comparisons
  according the Anthony Bucci's dimensions extraction method from:

    Bucci, Pollack, & de Jong (2004).  "Automated Extraction
    of Question Structure".  In Proceedings of the 2004 Genetic
    and Evolutionary Computation Conference.

  The routine returns a list of dimensions.  Each dimension
  corresponds to an underlying objective of the question.  The
  dimension is itself a list of tests such that:

    1) All tests in a given dimension are comparable; and
    2) They are ordered in terms of Pareto dominance.
  """
  dimensions = []

  for test in filteredTests:
    wasInserted = False
    dimIdx = 0
    for dim in dimensions:
      comparable, compareValue = mooCompare(dim[-1][0],test[0])
      if comparable:
        # The dimensions must be inserted at the end or there will
        # be comparison questions because of boundary cases (e.g.,
        # when all tests are passed or failed, etc.)
        dim.append(test)
        wasInserted = True
        break
      dimIdx += 1
     
      #      wasInserted = insertTestIntoDimension(dim,test)
    if not wasInserted:
      dimensions.append( [test] )

  # We appended tests to the end, so the axes are backward.  Fix
  # this so that they are ordered correctly.
  for dim in dimensions:
    dim.sort(key=lambda x: x[1])

  # The data structure that is returned is a list of each axis (dimension) with the
  # tests embedded into these dimensions as lists of tuples, ordered by the number
  # of passes or fails.  In the case of Questions, each axis is ordered from the test
  # that fewer students fail to the Question where more students fail ... but all 
  # Questions along an axis are comparable.  In the case of the students, each axis
  # is ordered from the student who passes the fewest Questions to the student who
  # passes the most.  Again, all students on an axis are comparable.  That is:  the
  # leaf nodes are always the most dominant questionts or students (depending on the
  # analysis)
    
  return dimensions



def getQuestionSet(dataset):
  questions = set()
  for student in dataset:
    for question in dataset[student]:
      questions.add(question)
  return question

def getStudentSet(dataset):
  return set(dataset.keys())
          

def extractDecaMatrixQuestionByStudent(filteredTests, questionSet, studentSet):
  questionList = list(questionSet)
  questionList.sort()
  studentList = list(studentSet)
  studentList.sort()

  LOGGER.info("")
  LOGGER.info("DECA-Style Question-by-Student Result Matrix:")
  LOGGER.info(str('').ljust(5), end='')
  for student in studentList:
    LOGGER.info(str(student).center(5), end='=')
  LOGGER.info("")
  
  for test in filteredTests:
    resultTuple, numCorrect, questionID = test
    LOGGER.info(str(questionID).ljust(5), end='')
    for test in resultTuple:
      if test:
        LOGGER.info('1'.center(5), end='')
      else:
        LOGGER.info('0'.center(5), end='')
    LOGGER.info("")
  LOGGER.info("")

  
def analyzeQuestions(dataset, whichScores, contextDict, quiet=False):
  """
  This function provides a dimension extraction based analysis of a dataset,
  under the assumption that we are extracting the dimensions of the underlying
  dimensions of the question sets.   
  """
  questionSubset = contextDict["questionSubset"]
  doMatrixExtraction = contextDict["doMatrixExtraction"]
  omitSpanned = contextDict["omitSpanned"]

  rawTests, pSet, sSet, questionEquivClass = cleanupForQuestionAnalysis(dataset, questionSubset)
  filteredTests = filterTests(rawTests, omitSpanned, quiet)
  
  if doMatrixExtraction:
    #extractDecaMatrixQuestionByStudent(filteredTests, pSet, sSet)
    dataUtils.extractMatrixStudentByQuestion(dataset)

  # Get the question dimensions
  studentDims = extractDimensions(filteredTests)
  numQuestions = len(pSet)

  # Get the informatively easy and informatively hard questions; RPW:  Dim extraction *twice*?  More efficient way?
  #rawStudent, pSetStudent, sSetStudent, studentEquivalenceClass = cleanupForStudentAnalysis(dataset, questionSubset)
  #questionDims = extractDimensions(filteredTests)
  #infHard, infEasy = summarizeMaxMinDimensions(questionDims, pSetStudent, studentEquivalenceClass, True)

  
  # Set the context dictionary up ... probably want equiv classes, etc.
  contextDict["numQuestions"] = numQuestions
  contextDict["equivClass"] = questionEquivClass
  contextDict["reductionRatio"] = (float(len(studentDims))/float(numQuestions))
  contextDict["questionSubset"] = pSet
  contextDict["studentSubset"] = sSet

  return studentDims


def analyzeStudents(dataset, whichScores, contextDict, quiet=False):
  """
  This function provides a dimension extraction based analysis of a dataset,
  under the assumption that we are extracting the dimensions of the underlying
  dimensions of the students.  

  Not all students will appear in this list.  If one student performed
  precisely indentically to another, one of these was removed.  This is done
  in all such cases to ensure there are only unique student/question result
  strings.
  """
  questionSubset = contextDict["questionSubset"]
  doMatrixExtraction = contextDict["doMatrixExtraction"]
  omitSpanned = contextDict["omitSpanned"]

  rawTests, pSet, sSet, studentEquivalenceClass = cleanupForStudentAnalysis(dataset, questionSubset)
  filteredTests = filterTests(rawTests, omitSpanned, quiet)
  
  ## <-- Add a routine to output the matrix  
  dims = extractDimensions(filteredTests)

  contextDict["numStudents"] = len(sSet)  
  contextDict["equivClass"] = studentEquivalenceClass # What is studentEquivalenceClassSize used for?
  contextDict["reductionRatio"] = (float(len(dims))/float(len(sSet)))
  contextDict["questionSubset"] = pSet
  contextDict["studentSubset"] = sSet

  return dims


def summarizeQuestionAnalysis(dims, numQuestions):
  """
  The result will be a print out of each separate question dimension, with each
  question in that dimension listed in order of Pareto dominance (the top one
  dominating the others, etc).  Also listed are the number of students who
  passed that test.
  """
  reductionRatio = (float(len(dims))/float(numQuestions))
  LOGGER.info("There are ", len(dims), "underlying objectives to this QUESTION data of", numQuestions, \
        "::", reductionRatio)
    
  for dim in dims:
    LOGGER.info("Count \tQuestion ID")
      
    for test in dim:
      LOGGER.info("  ", test[1], "\t", test[2])  
    LOGGER.info("")

  return len(dims)


def summarizeStudentAnalysis(dims, numStudents, studentEquivalenceClass):
  """
  Print out the results of dimension extraction for the sutdent analysis. The
  result will be a print out of each separate student dimension, with each
  student in that dimension listed in order of Pareto dominance (the top one
  dominating the others, etc).  Also listed are the number of questions passed
  by that student.  In addition, a binary vector is printed indicating which
  tests were passed.
  """
  reductionRatio =  (float(len(dims))/float(numStudents))
  LOGGER.info("There are ", len(dims), "underlying objectives to this STUDENT data of", numStudents, \
        "::", reductionRatio)
        
  for dim in dims:
    LOGGER.info("Count \t Cases\t\tStudent ID")
    for test in dim:
      LOGGER.info("  ", test[1], "\t", end='')
      
      for idx in range(len(test[0])):
        if test[0][idx]:
          sys.stdout.write('1')
        else:
          sys.stdout.write('0')
          
      LOGGER.info('\t', test[2], end='')
      
      count = len(studentEquivalenceClass[test[0]])
      if (count > 1):
        LOGGER.info("[" + str(len(studentEquivalenceClass[test[0]])) + "]")
      else:
        LOGGER.info("")
      
    LOGGER.info("")

  return len(dims), numStudents


def printOneLine(prefix, prefixWidth, values, valWidth):
  n = len(values)
  LOGGER.info(prefix.ljust(prefixWidth), end='')
  for idx in range(n):
    LOGGER.info( (str(values[idx])).center(valWidth), end='')
  LOGGER.info("")

def printSeparator(prefixWidth, n, valWidth):
  LOGGER.info("".ljust(prefixWidth), end='')
  for idx in range(n):
    LOGGER.info(''.center(valWidth,'='), end='')
  LOGGER.info("")


def summarizeMaxMinDimensions(studentDims, testSubset, studentEquivalenceClass, quiet=True):
  """
  This function attempts to provide some feedback about difficulty.  It optimizes two things.
    1. It looks across all dimensions of *learners*, finds the best learner in that dimension,
       then keeps track of which questions were *missed* by these learners.  It reports how many
       *fails* each test got with the *best* learner of each dimension as a measure of *difficulty*.
    2. It looks across all dimensions of *learners*, finds the worst learner in that dimension,
       then keeps track of which questions were *passed* by these learners.  It reports how many
       *successes* each test got with the *worst* learner of each dimension as a measure of *ease*.
  In essence:  the hardest test is the one that the best learners failed the most and the easiest
               test is the one that the worst learners passed the most.
  """
  # Initialize histograms
  n = len(testSubset)
  hardHist  = [0] * n
  hardCount = [0] * n
  easyHist  = [0] * n
  easyCount = [0] * n
  easySet = set()
  hardSet = set()
  
  for dim in studentDims:
    # The "Best" learner in this dimension is the one who passed the most questions
    # for that dimension (the leaf node)
    # The "Worst" learner in this dimension is the one who passed the fewest
    # questions for that dimension (the root node)
    bestLearnerInDim = dim[-1]
    worstLearnerInDim = dim[0]

    # Loop through each pass/fail result in the vector of questions/templates taken
    # by the students
    for idx in range(n):
      # If the BEST learner FAILED this one, count it toward "difficult"
      if not bestLearnerInDim[0][idx]:
        hardHist[idx] += 1
        hardCount[idx] += len(studentEquivalenceClass[bestLearnerInDim[0]])

      # If the WORST learner PASSED this one, count it toward "easy"
      if worstLearnerInDim[0][idx]:
        easyHist[idx] += 1
        easyCount[idx] += len(studentEquivalenceClass[worstLearnerInDim[0]])
        
  # Print the difficulty measures across the questions, but only if the "quiet" flag 
  # is not on.  The function is "quiet" by default.
  if (not quiet):
      # Print header
      testList = list(testSubset)

      printOneLine("",10,testList,5)
      printSeparator(10,n,5)

      maxVal = max(hardHist)
      hardSet = set()
      LOGGER.info("InfHrdHst".ljust(10), end='')
      for idx in range(n):
        if hardHist[idx] == maxVal:
          LOGGER.info( ("*"+str(hardHist[idx])).center(5), end='')
          hardSet.add(testList[idx])
        else:
          LOGGER.info(str(hardHist[idx]).center(5), end='')
      LOGGER.info("")

      #hardRanks = stats.rankdata(hardHist)
      printOneLine("InfHrdCnt",10,hardCount,5)
      printSeparator(10,n,5)

      # Print the simplicity measures across the questions
      maxVal = max(easyHist)
      easySet = set()
      LOGGER.info("InfEsyHst".ljust(10), end='')
      for idx in range(n):
        if easyHist[idx] == maxVal:
          LOGGER.info( ("*"+str(easyHist[idx])).center(5), end='')
          easySet.add(testList[idx])
        else:
          LOGGER.info(str(easyHist[idx]).center(5), end='')
      LOGGER.info("")

      #easyRanks = stats.rankdata(easyHist)
      printOneLine("InfEsyCnt",10,easyCount,5)
      printSeparator(10,n,5)

  # Still need to build the sets, even if we aren't reporting them
  else:
      testList = list(testSubset)

      maxVal = max(hardHist)
      hardSet = set()
      for idx in range(n):
        if hardHist[idx] == maxVal:
          hardSet.add(testList[idx])

      maxVal = max(easyHist)
      easySet = set()
      for idx in range(n):
        if easyHist[idx] == maxVal:
          easySet.add(testList[idx])

  return hardSet, easySet


def completeAnalysisWithReport(dataset, questionSubset=set(), prefixStr="SUMMARY", doMatrixExtraction=False, omitSpanned=True):
  # Gather all unique questions and students
  baselineQuestionSet = set()
  baselineStudentSet = set()
  for studentID in dataset:
    baselineStudentSet.add(studentID)
    for questionID in dataset[studentID]:
      baselineQuestionSet.add(questionID)

  contextDict = {"questionSubset":questionSubset,
                 "doMatrixExtraction":doMatrixExtraction,
                 "omitSpanned":omitSpanned}

  LOGGER.info("")
  LOGGER.info("Question Dimensional Analysis:".upper())
  LOGGER.info(''.ljust(70,'-'))
  LOGGER.info("  Each grouping below represents a distinct 'concept' discovered in the question data.") 
  LOGGER.info("  The questions in that dimension are listed in Pareto dominance order, such that the")
  LOGGER.info("  top question strictly dominates the ones under it.  Only the top-most question in")
  LOGGER.info("  each dimension provides any *distinctions* in student performance.")
  LOGGER.info(''.ljust(70,'-'))
  questionDims = analyzeQuestions(dataset, "both", contextDict)
  numQuestions = contextDict['numQuestions']
  numProbDims = summarizeQuestionAnalysis(questionDims,numQuestions)
  LOGGER.info("")
  cytoStr = dataUtils.convertDecaQuestionDimsToCytoElementDict(questionDims)
  LOGGER.info("Cytoscape structure: ", cytoStr)
  LOGGER.info("")

  # If you aren't specifying particular questions, just use them all
  if len(questionSubset) == 0:
    questionSubset = baselineQuestionSet

  LOGGER.info("Student Dimensional Analysis:".upper())
  LOGGER.info(''.ljust(70,'-'))
  LOGGER.info("  Each grouping below represents a distinct 'type' of student performance discovered")
  LOGGER.info("  The students in that dimension are listed in Pareto dominance order, such that the")
  LOGGER.info("  top student strictly dominates the ones under it.  The top student in each group")
  LOGGER.info("  might be seen as the one who mastered that concept the best, while the bottom might")
  LOGGER.info("  be seen as the one who mastered it the least.")
  LOGGER.info(''.ljust(70,'-'))
  studentDims = analyzeStudents(dataset, "both", contextDict)
  numStudents = contextDict['numStudents']
  studentEquivalenceClass = contextDict['equivClass']
  numStudentDims = summarizeStudentAnalysis(studentDims, numStudents, studentEquivalenceClass)
  LOGGER.info("")

  LOGGER.info("Question Difficulty Analysis (*):".upper())
  LOGGER.info(''.ljust(70,'-'))
  LOGGER.info("  For the 'Hard' row, we count the number of times the *best* student")
  LOGGER.info("  in each dimension misses that Question.  The bigger the number, the harder.")
  LOGGER.info("")
  LOGGER.info("  For the 'easy' row, we count the number of times the *worst* student")
  LOGGER.info("  in each dimension passes that Question.  The bigger the number, the easier.")
  LOGGER.info("")
  LOGGER.info("  The optima in each case is indicated by '*'.")
  LOGGER.info(''.ljust(70,'-'))
  hardSet, easySet = summarizeMaxMinDimensions(studentDims, questionSubset, studentEquivalenceClass, False)
  
  questionList = list(questionSubset)
  tradHardHist = dataUtils.simpleDifficultyEstimate(dataset, questionList)
  tradHard = [] 
  for prob in questionList:
    tradHard.append(tradHardHist[prob])
    
  printOneLine("TradHard",10,tradHard,5)
  printSeparator(10,len(tradHard),5)

  # A final summary line that's easy to grep by "prefix"
  LOGGER.info((prefixStr + ";").ljust(20), \
        (str(numProbDims) + ";").ljust(10), \
        (str(numQuestions) + ";").ljust(10), \
        (str(numStudentDims) + ";").ljust(10), \
        (str(numStudents) + ";").ljust(10), \
        (", ".join(str(e) for e in hardSet)) + ";", \
        "     ", \
        (", ".join(str(e) for e in easySet)) )
                  
  return questionDims, studentDims


if __name__ == '__main__':
  LOGGER.info("")
  LOGGER.info('='.ljust(50,'='))
  LOGGER.info("Running the DECA unit test ...")
  LOGGER.info("")

  # The user can specify an INI file with the desired configuration
  configFileName = ""
  if (len(sys.argv) > 1):
    configFileName = sys.argv[1].strip()
  
  # Configuration parameters for command line and INI file
  configDefaults = {"doMatrixExtraction":False,\
                    "omitSpanned":True}
  
  #configObj = configReader.buildArgObject(configFileName,'QuestionAnalysis',configDefaults,False)
  
  # Generate fake data to convert
  StudentIDs    = pd.Series([1,2,3,4, 1,2,3,4, 1,2,3,4, 1,2,3,4, 1,2,3,4], dtype='int')
  QuestionIDs   = pd.Series([1,1,1,1, 2,2,2,2, 3,3,3,3, 4,4,4,4, 5,5,5,5], dtype='int')
  InitialScores = pd.Series([0,0,1,1, 0,1,1,1, 1,1,1,0, 0,1,0,1, 1,0,1,1], dtype='float')
  RevisedScores = pd.Series([], dtype='float')

  df = pd.DataFrame({'StudentID':StudentIDs, \
                     'QuestionID':QuestionIDs, \
                     'InitialScore':InitialScores, \
                     'RevisedScore':RevisedScores})

  #df = da.GetScoresDataframe(0, 5)
  dataset = dataUtils.convertDFToDecaResultsFormat(df)

  completeAnalysisWithReport(dataset,set(), "SUMMARY", True, True)

  LOGGER.info("")
  LOGGER.info("... Ending the DECA unit test")
  LOGGER.info('='.ljust(50,'='))
  LOGGER.info("")
