const updateQuiz = (qid, settings) => 
    fetch('/grades/' + qid + '/settings',{
        method:         'POST',
        headers:        {'Content-Type' : 'application/json'},
        body:           JSON.stringify(settings),
        credentials:    'same-origin'
    })      

const onSettingChange = (qid, settingName, cb = false) => async (e) => {
    try {
        let selectedValue = parseInt(e.target.value);
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

const createWeightSlider = (qid, sliderId, weights, cb, step1WeightElId = "step1-weight", step2WeightElId = "step2-weight", justWeightElId = "justification-weight", partWeightElId = "participation-weight") => {
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
            tip: "Weight of justifications: |diff|%. Weight of participation: |leftValue|%"
        }
        ], maxValue: 100,
        cb: function (values) {
            let weights = values.map((v, i) => v - (values[i - 1] || 0));
            weights.push(100 - values[values.length - 1]);
            [ weights.initialScoreWeight, weights.revisedScoreWeight, weights.justificationWeight, weights.participationWeight ] = weights;
            document.getElementById(step1WeightElId).innerHTML = weights.initialScoreWeight
            document.getElementById(step2WeightElId).innerHTML = weights.revisedScoreWeight
            document.getElementById(justWeightElId).innerHTML = weights.justificationWeight
            document.getElementById(partWeightElId).innerHTML = weights.participationWeight
            clearTimeout(tableUpdateTimeout)
            tableUpdateTimeout = setTimeout(async () => {
                try {
                    await updateQuiz(qid, {"initial_score": weights.initialScoreWeight, "revised_score": weights.revisedScoreWeight, "justification_grade": weights.justificationWeight, "participation_grade": weights.participationWeight})
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
