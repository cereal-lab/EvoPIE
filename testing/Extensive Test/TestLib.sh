#!/bin/bash

function header {
    echo -e "\n---> $1\n"
}

function curlit {
    LOGIN="-L -b ./mycookies"
    MSG=$1
    TARGET_PATH=$2
    DATA=$3
    if [[ -z $DATA ]]
    then 
        METHOD='-X GET'
    else
        METHOD=''
        # NOTE do not use -X POST here or the signup requests will POST to /login
        # right after instead of sending a GET to /login
    fi

    curl $LOGIN $METHOD -d "$DATA" -H "Content-Type: application/json" "http://127.0.0.1:5000$TARGET_PATH" &>/dev/null
    if [[ $? == 0 ]]
    then
        echo -e "\t$MSG"
    else
        echo -e "\t$MSG --> Status returned is $?"
        exit
    fi
}

function like {
    LOGIN="-L -b ./mycookies"
    MSG="Liking Justification --> $1"
    TARGET=$2
    METHOD='-X PUT'

    curl $LOGIN $METHOD -d "$DATA" -H "Content-Type: application/json" "http://127.0.0.1:5000/justification/${TARGET}/like" &>/dev/null
    if [[ $? == 0 ]]
    then
        echo -e "\t$MSG"
    else
        echo -e "\t$MSG --> Status returned is $?"
        exit
    fi
}

function curl_login {
    MSG=$1
    DATA=$2
    
    curl -X POST -c ./mycookies -d "$DATA" -H "Content-Type: application/json" "http://127.0.0.1:5000/login" &> /dev/null
    if [[ $? == 0 ]]
    then
        echo -e "\tLogged in as $MSG"
    else
        echo -e "\tFAILED to login as $MSG"
        exit
    fi
}

function curl_grades {
    # curl --silent -b ./mycookies -X GET -H "Content-Type: application/json" "http://127.0.0.1:5000/grades/1/justificationGrade"
    RES=$(curl --silent -b ./mycookies -X GET -H "Content-Type: application/json" "http://127.0.0.1:5000/grades/1/justificationGrade")
    if [[ $RES =~ \{[^\}]*?\} ]]; then
        justification_grade=${BASH_REMATCH[0]} 
        RES=${RES/"${BASH_REMATCH[0]}"/}
    fi
    if [[ $RES =~ \{[^\}]*?\} ]]; then
        total_scores=${BASH_REMATCH[0]} 
    fi
    # echo "$justification_grade || $total_scores"
}

function curl_download {
    #LOGIN="-L -b ./mycookies"
    MSG=$1
    TARGET_PATH=$2
    LOCAL_FILE=$3
    curl_grades
    DATA="{ \"justification_grade\": $justification_grade, \"total_scores\": $total_scores}"
    # METHOD='-X GET'
    # echo "$DATA"
    curl --silent -b ./mycookies -X POST -d "$DATA" --output "$LOCAL_FILE" -H "Content-Type: application/json" "http://127.0.0.1:5000$TARGET_PATH"
    if [[ $? == 0 ]]
    then
        echo -e "\t$MSG"
    else
        echo -e "\t$MSG --> Status returned is $?"
        exit
    fi
}