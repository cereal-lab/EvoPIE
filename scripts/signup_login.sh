#signup
curl -L -d '{ "email": "alessio3@usf.edu", "password": "secret3", "firstname": "first3", "lastname": "last3" }' -H 'Content-Type: application/json'  http://localhost:5000/signup &> /dev/null && echo "signup"

#login
curl -L -c ./mycookies -d '{ "email": "alessio3@usf.edu", "password": "secret3"}' -H 'Content-Type: application/json'  http://localhost:5000/login &> /dev/null && echo "login"

#test accessing something while logged in
curl -L -b ./mycookies http://localhost:5000/quizquestions && echo



