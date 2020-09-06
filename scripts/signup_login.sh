#signup
curl -L -d '{ "email": "alessio1@usf.edu", "password": "secret1", "firstname": "first1", "lastname": "last1" }' -H 'Content-Type: application/json'  http://localhost:5000/signup &> /dev/null && echo "signup"
curl -L -d '{ "email": "alessio2@usf.edu", "password": "secret2", "firstname": "first2", "lastname": "last2" }' -H 'Content-Type: application/json'  http://localhost:5000/signup &> /dev/null && echo "signup"
curl -L -d '{ "email": "alessio3@usf.edu", "password": "secret3", "firstname": "first3", "lastname": "last3" }' -H 'Content-Type: application/json'  http://localhost:5000/signup &> /dev/null && echo "signup"

#login
curl -L -c ./mycookies -d '{ "email": "alessio1@usf.edu", "password": "secret1"}' -H 'Content-Type: application/json'  http://localhost:5000/login &> /dev/null && echo "login"
#FIXME for now, we hardcode that user id 1 is an instructor, fix that later.

#test accessing something while logged in
curl -L -b ./mycookies http://localhost:5000/quizquestions && echo
