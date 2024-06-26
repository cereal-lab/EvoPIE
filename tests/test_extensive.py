import pytest 
import json
from evopie import APP
import logging

@pytest.fixture()
def app():
    APP.config.update({
        "TESTING": True,
    })
    yield APP

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()    

@pytest.mark.parametrize("settings, fileName", 
[
    ({"fq": 1, "sq": 3, "tq": 5, "frq": 10, "is": 40, "rs": 30, "jg": 20, "pg": 10}, "LF_50%_Likes_15_to_19_QP_1_3_5_10_Weights_40%_30%_20%_10%.csv"),
    ({"fq": 1, "sq": 3, "tq": 5, "frq": 10, "is": 60, "rs": 20, "jg": 10, "pg": 10}, "LF_50%_Likes_15_to_19_QP_1_3_5_10_Weights_60%_20%_10%_10%.csv"),
    ({"fq": 2, "sq": 5, "tq": 8, "frq": 10, "is": 40, "rs": 30, "jg": 20, "pg": 10}, "LF_50%_Likes_15_to_19_QP_2_5_8_10_Weights_40%_30%_20%_10%.csv"),
    ({"fq": 2, "sq": 5, "tq": 8, "frq": 10, "is": 60, "rs": 20, "jg": 10, "pg": 10}, "LF_50%_Likes_15_to_19_QP_2_5_8_10_Weights_60%_20%_10%_10%.csv")
])
def test_extensive(runner, settings, fileName):
    res = runner.invoke(args=["DB-reboot"])
    assert res.exit_code == 0
    #TODO: add assert that db is empty

    res = runner.invoke(args=["course", "init", "-n", "COP 3000 SPRING", "-t", "Test Course for Comp Sci", "-d", "This is a test course for the Comp Sci department at USF."])
    assert res.exit_code == 0

    res = runner.invoke(args=["course", "init", "-n", "COP 3000 FALL", "-t", "Test Course for Comp Sci", "-d", "This is a test course for the Comp Sci department at USF."])
    assert res.exit_code == 0

    res = runner.invoke(args=["quiz", "init", "-cid", 1, "-nq", 5, "-nd", 4, "-qd", json.dumps({"2":[5,6,7],"3":[9,10,11],"4":[13,14,16]}), "-s", json.dumps(settings)])
    assert res.exit_code == 0
    APP.logger.info(res.stdout)
    #TODO: add assert that quiz is inited 

    res = runner.invoke(args=["quiz", "copy", "-q", 1, "-cid", 2])
    assert res.exit_code == 0

    res = runner.invoke(args=["quiz", "settings", "-q", 2, "-s", json.dumps({"fq": 1, "sq": 3, "tq": 5, "frq": 10, "is": 40, "rs": 30, "jg": 20, "pg": 10})])
    assert res.exit_code == 0
    
    res = runner.invoke(args=[ "student", "init", "-cid", 1, "-ns", 20, "--exclude-id", 12, "-ef", 'student{}@usf.edu' ])
    assert res.exit_code == 0
    APP.logger.info(res.stdout)

    res = runner.invoke(args=[ "student", "addToCourse", "-cid", 2])
    
    knowledge = [{"sid":{"range":[1,4]},"qid":1,"did":3,"step":1,"metrics":{"chance":1}}, 
        {"sid":{"ranges":[[1,4],[10,18]]},"qid":2,"did":7,"step":1,"metrics":{"chance":1}}, 
        {"sid":{"range":[1,9]},"qid":3,"did":11,"step":1,"metrics":{"chance":1}}, 
        {"sid":{"range":[1,9]},"qid":4,"did":13,"step":1,"metrics":{"chance":1}}, 
        {"sid":{"range":[1,18]},"qid":5,"did":17,"step":1,"metrics":{"chance":1}}, 
        {"sid":{"range":[1,14]},"qid":1,"did":4,"step":2,"metrics":{"chance":1}}, 
        {"sid":{"ranges":[[1,7],10]},"qid":4,"did":13,"step":2,"metrics":{"chance":1}}, 
        {"sid":{"range":[1,14]},"qid":5,"did":17,"step":2,"metrics":{"chance":1}}]
    res = runner.invoke(args=[ "student", "knows", "-kr", "-ef", 'student{}@usf.edu', *[ v for k in knowledge for v in ["-k", json.dumps(k)]] ])

    assert res.exit_code == 0
    APP.logger.info(res.stdout)

    likes = [{"sid":1,"jid":{"range":[90,103]}}, 
        {"sid":2,"jid":{"range":[90,104]}},
        {"sid":3,"jid":{"range":[89,104]}},
        {"sid":4,"jid":{"range":[89,105]}},
        {"sid":5,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57]}},
        {"sid":6,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33]}},
        {"sid":7,"jid":{"ranges":[[1,9],[23,27],17,22,30,33,57]}},
        {"sid":{"range":[8,9]},"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,67,68]}},
        {"sid":10,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,[67,71],[89,104]]}},
        {"sid":{"range":[11,14]},"jid":{"ranges":[[1,9],26,27,17,22,24,30,33,37,57,67,71,[89,91],[95,104]]}},
        {"sid":{"range":[15,19]},"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,[67,71],[89,101]]}},
        {"sid":20,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,[67,71],[89,115]]}}]
    res = runner.invoke(args=[ "quiz", "run", "-q", 1, "-cid", 1, "-s", "STEP1", "-s", "STEP2", 
                            "--no-algo", "--justify-response", "-ef", 'student{}@usf.edu', '-kns', 'KNOWLEDGE_SELECTION_CHANCE',
                            *[ v for l in likes for v in ["-l", json.dumps(l)]]])        
    #TODO: add assert for run
    assert res.exit_code == 0
    APP.logger.info(res.stdout)

    res = runner.invoke(args=[ "quiz", "result", "-q", 1,
                            "--expected", "tests/{}".format(fileName)])        
    APP.logger.info(res.stdout)
    assert res.exit_code == 0


