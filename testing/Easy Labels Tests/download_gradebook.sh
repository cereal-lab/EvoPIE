#!/bin/bash

# PRE-REQUISITES
#   ./setup.sh
#   ./step1.sh --> optional
#   ./step2.sh --> optional



source ./TestLib.sh

#login as INSTRUCTOR to release quiz in step #2
curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "pwd" }'
curldownload    "Downloading CSV gradebook"        "/getDataCSV/1"



