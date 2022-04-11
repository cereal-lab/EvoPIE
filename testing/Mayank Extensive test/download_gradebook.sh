#!/bin/bash

# PRE-REQUISITES
#   ./setup.sh
#   ./step1.sh --> optional
#   ./step2.sh --> optional
#   we need a ./gradebook-verified.csv file that will be used to assert the correctness of the downloaded file
#   This csv will have hand-calculated values based on all the operations we performed in step1 / step2 
#   before to download the CSV.


source ./TestLib.sh

rm ./gradebook-downloaded.csv ./gradebooks.diff

#login as INSTRUCTOR to download the gradebook and verify that it is correct
curl_login                              "instructor"            '{ "email": "instructor@usf.edu", "password": "pwd" }'
curl_download    "Downloading gradebook" "/getDataCSV/1"         "gradebook-downloaded.csv"

header "Comparing downloaded gradebook to reference one for these tests"

diff ./gradebook-downloaded.csv ./Extensive-Test-75%-Limiting-4-3-2-1-and-38-likes.csv > ./gradebooks.diff
if [[ $? -eq 0 ]]
then
    echo "Test SUCCESSFUL - the CSV files are identical"
else
    echo " Test FAILED - the CSV files are different. Check out ./gradebooks.diff for details."
fi
