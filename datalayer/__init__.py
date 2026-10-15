import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os


DB = None
def StartupDatabase(application):
    global DB

    if (application == None):
        DB = SQLAlchemy()
    else:
        DB = SQLAlchemy(application)

    return DB

LOGGER = None

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def ConfigureLogger(logger):
    level_name = os.getenv("EVOPIE_LOG_LEVEL", "INFO").upper()
    level = LOG_LEVELS.get(level_name)
    if level is None:
        raise ValueError(
            "EVOPIE_LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR, "
            "or CRITICAL."
        )

    logger.setLevel(level)
    if not logger.handlers and not logging.getLogger().handlers:
        logger.addHandler(logging.StreamHandler())
    return logger


def RegisterGlobalLogger(appLogger):
    global LOGGER
    LOGGER = ConfigureLogger(appLogger)
    return LOGGER

#quiz attempt states 
QUIZ_HIDDEN = "HIDDEN"
QUIZ_ATTEMPT_STEP1 = QUIZ_STEP1 = "STEP1" #when student attempt on STEP1 - it means that student is going to take step1 
QUIZ_ATTEMPT_STEP2 = QUIZ_STEP2 = "STEP2" #when student attempt on STEP2 - student finished step1 and ready to take step2
QUIZ_ATTEMPT_STEP3 = QUIZ_STEP3 = "STEP3" #when student attempt on STEP3 - student finished step2 and ready to take step3
QUIZ_ATTEMPT_SOLUTIONS = QUIZ_SOLUTIONS = "SOLUTIONS" #when student attempt on SOLUTIONS - student finished step1 and step2 and ready to see solutions

attempt_next_steps = {QUIZ_ATTEMPT_STEP1: QUIZ_ATTEMPT_STEP2, QUIZ_ATTEMPT_STEP2: QUIZ_ATTEMPT_SOLUTIONS, QUIZ_ATTEMPT_STEP3: QUIZ_ATTEMPT_SOLUTIONS}

def get_attempt_next_step(cur_step):
    return attempt_next_steps.get(cur_step, cur_step)

#system roles
ROLE_STUDENT = "STUDENT"
ROLE_INSTRUCTOR = "INSTRUCTOR"
ROLE_ADMIN = "ADMIN"
# ROLE_RESEARCHER = "RESEARCHER"

