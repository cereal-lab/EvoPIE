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

    curl $LOGIN $METHOD -d "$DATA" -H "Content-Type: application/json" "http://127.0.0.1:5000$TARGET_PATH" 
    #&>/dev/null
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
    
    TARGET_PATH="/login"
    
    curl -L -c ./mycookies -d "$DATA" -H "Content-Type: application/json" "http://127.0.0.1:5000$TARGET_PATH" &>/dev/null
    if [[ $? == 0 ]]
    then
        echo -e "\tLogged in as $MSG"
    else
        echo -e "\tFAILED to login as $MSG"
        exit
    fi
}

