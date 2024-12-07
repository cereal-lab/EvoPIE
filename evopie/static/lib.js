const updateQuiz = (qid, settings) => 
    fetch('/quiz/' + qid + '/settings',{
        method:         'POST',
        headers:        {'Content-Type' : 'application/json'},
        body:           JSON.stringify(settings),
        credentials:    'same-origin'
    })      

const onSettingChange = (qid, settingName, cb = false, preprocess = parseInt) => async (e) => {
    try {
        let selectedValue = preprocess(e.target.value);
        await updateQuiz(qid, {[settingName]:  selectedValue})
        if (cb === false) window.location.reload();
        else {
            await cb(qid);
        }
    } catch (e) {
        console.error(e);
        //TODO: UI message
    }
}                

const createWeightSlider = (qid, sliderId, weights, cb, step1WeightElId = "step1-weight", step2WeightElId = "step2-weight", 
                                justWeightElId = "justification-weight", partWeightElId = "participation-weight", 
                                designWeightElId = "designing-weight") => {
    let tableUpdateTimeout = null
    let slider = createSlider(sliderId, { values: [
        {
            value: weights.initialScoreWeight,
            label: "|value|",
            step: 5,
            tip: "Weight of step #1 attempt: |diff|%"
        },
        {
            value: weights.initialScoreWeight + weights.revisedScoreWeight,
            label: "|value|",
            step: 5,
            tip: "Weight of step #2 attempt: |diff|%"
        },
        {
            value: weights.initialScoreWeight + weights.revisedScoreWeight + weights.justificationWeight,
            label: "|value|",
            step: 5,
            tip: "Weight of justifications: |diff|%"
        },
        {
            value: weights.initialScoreWeight + weights.revisedScoreWeight + weights.justificationWeight + weights.participationWeight,
            label: "|value|",
            step: 5,
            tip: "Weight of participation: |diff|%. Weight of distractor designing: |leftValue|%"
        }
        ], maxValue: 100,
        cb: function (values) {
            let weights = values.map((v, i) => v - (values[i - 1] || 0));
            weights.push(100 - values[values.length - 1]);
            [ weights.initialScoreWeight, weights.revisedScoreWeight, weights.justificationWeight, weights.participationWeight, weights.designingWeight ] = weights;
            document.getElementById(step1WeightElId).innerHTML = weights.initialScoreWeight
            document.getElementById(step2WeightElId).innerHTML = weights.revisedScoreWeight
            document.getElementById(justWeightElId).innerHTML = weights.justificationWeight
            document.getElementById(partWeightElId).innerHTML = weights.participationWeight
            document.getElementById(designWeightElId).innerHTML = weights.designingWeight
            clearTimeout(tableUpdateTimeout)
            tableUpdateTimeout = setTimeout(async () => {
                try {
                    await updateQuiz(qid, {"initial_score": weights.initialScoreWeight, "revised_score": weights.revisedScoreWeight, "justification_grade": weights.justificationWeight, "participation_grade": weights.participationWeight, "designing_grade": weights.designingWeight})
                    await cb(qid)
                } catch (e) {
                    //TODO: render error on UI
                    console.error(e)
                }
            }, 400) //this will update everything after period of inactivity
        }
    })
    return slider;
}

function sendToFlashLand(message, type) {
    var target = document.getElementById('flashland')
    var data = document.createElement('div')
    var alertEl = document.createElement('div')
    alertEl.classList.add('alert', 'mb-1', 'py-1', 'alert-' + type, 'alert-dismissible', 'fade', 'show')
    alertEl.role = 'alert'
    alertEl.innerHTML = 
        message 
        + '<button type="button" class="small py-2 btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'
    data.append(alertEl)
    target.append(data)
    var bootstrapAlert = new bootstrap.Alert(alertEl)
    setTimeout(() => bootstrapAlert.close(), 5000)
}

const fetchJson = async (...args) => {
    try {
        const response = await fetch(...args)
        const data = await response.json()
        if (response.status >= 400) {
            console.error("[fetch] fails: ", response.status, args, data)
            sendToFlashLand(data.message, "danger");
            throw new Error(data.message) //this exists to shortcut and exit event handler - otherwise return null and deal with it outside
        } else {
            return data;
        }
    } catch (e) {
        //we show error in flash area
        console.error("[fetch] fails: ", args, e)
        sendToFlashLand("Something went wrong. Could not save state.", "danger")
        throw e;
    }
}

/** Delays function execution for some time  */
const debounce = (func, timeout = 300) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(async () => { await func(...args); }, timeout);
    };
}

const delay = ms => new Promise(res => setTimeout(res, ms));

const buildQuizSaver = (quizId, courseId, quizFormId) => {
    const saveAnswers = async () => {
        const form = new FormData(document.getElementById(quizFormId))
        const data = {};
        for (const [name, value] of form.entries()) {
            if (name.startsWith("question_")) data[name.split("_")[1]] = parseInt(value)
        }
        const {} = await fetchJson(`/quizzes/${quizId}/${courseId}/answers`, {
            method: 'PUT',
            headers: {'Content-Type' : 'application/json'},
            body: JSON.stringify(data),
            credentials: 'same-origin'
        })            
    }
    return saveAnswers
}