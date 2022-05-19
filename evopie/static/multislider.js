/* component for rendering mulivalue slider 
*/

/**
 * Creates multi-value slider (horizontal)
 * @param {*} selector - DOM selector where slider should be instantiated
 * @param {*} options - includes:
 *      values - array of initial values, value is object with props:
 *                  value: initial value
 *                  step: value step 
 *                  label: text on handle 
 *                  tip: if provided - tip for handle
 *      maxValue - max possible value
 * Width of the slider is defined by parent component
 * @returns slider object (TODO - describe slider API)
 */
function createSlider(selector, {values, maxValue, cb}) {
    const host = document.querySelector(selector)
    if (!host) {
        console.warn("Selector not found for slider: " + selector);
        return null;
    }
    //drawing part - we style everything with multislider.css
    let holder = document.createElement("div")
    holder.classList.add("slider-holder");
    host.appendChild(holder);
    let sliderWidth = host.offsetWidth
    let line = document.createElement("div")
    line.classList.add("slider-line")
    holder.appendChild(line)
    let activeHandle = null
    const renderLabel = (handle) => {
        const label = handle.sl_label
        if (label) {
            let value = handle.sl_value
            const localMinValue = handle.sl_prev ? handle.sl_prev.sl_value : 0;    
            lavelVal = label.replace("|value|", value).replace("|diff|", value - localMinValue)
            handle.innerHTML = lavelVal
        }
    }
    const renderTip = (handle) => {
        if (handle.sl_tip) {
            let value = handle.sl_value
            const localMinValue = handle.sl_prev ? handle.sl_prev.sl_value : 0;    
            tip = handle.sl_tip.replace("|value|", value).replace("|diff|", value - localMinValue).replace("|leftValue|", Math.round(maxValue - value))
            handle.setAttribute("title", tip);
        }
    }
    const setHandlePos = (handle, newValue, shouldForce) => {        
        const step = handle.sl_step        
        let value = newValue || handle.sl_value
        const localMinValue = handle.sl_prev ? handle.sl_prev.sl_value : 0;
        const localMaxValue = handle.sl_next ? handle.sl_next.sl_value : maxValue;
        if (step) {
            let newValue = Math.round(value / step) * step; //round value to closest quant             
            if ((newValue == handle.sl_value) && !shouldForce) return;
            value = newValue;
        }
        if (value < localMinValue) value = localMinValue
        else if (value > localMaxValue) value = localMaxValue
        value = Math.round(value)
        handle.sl_value = value
        renderLabel(handle)
        renderTip(handle)
        for (let i = handle.sl_i + 1; i < handle.sl_handles.length; i++) {
            renderLabel(handle.sl_handles[i])
            renderTip(handle.sl_handles[i])
        }
        let pos = (value * sliderWidth / maxValue);
        handleWidth = handle.offsetWidth;
        handle.sl_pos = pos;
        handle.style.left = (pos - handleWidth / 2) + "px"; //we use absolute positioning
    }
    let handles = values.map(({value, step, label, tip}, i) => {
        let handle = document.createElement("div")
        handle.classList.add("slider-handle")
        handle.classList.add("slider-handle-" + i)            
        handle.sl_step = step;
        handle.sl_label = label;
        handle.sl_tip = tip;     
        handle.sl_value = value;   
        handle.addEventListener("mousedown", (e) => {
            if ((e.button != 0) || activeHandle) return;
            handle.classList.add("active")
            activeHandle = handle
        })
        handle.addEventListener("mouseup", (e) => {
            if (e.button != 0) return;
            handle.classList.remove("active")
            activeHandle = null
        }) 
        holder.appendChild(handle)
        return handle
    })
    handles.forEach((handle, i) => {
        if (typeof(handles[i-1]) != "undefined") { //not first handle
            handle.sl_prev = handles[i-1]
        }
        if (typeof(handles[i+1]) != "undefined") { //not last handle
            handle.sl_next = handles[i+1]
        }        
        handle.sl_handles = handles
        handle.sl_i = i
        setHandlePos(handle, handle.sl_value, true)
    })
    holder.addEventListener("mousemove", (e) => {
        if (!activeHandle || (activeHandle == e.target)) return; 
        let pos = e.offsetX;
        if (e.target.sl_handles) {
            if ((e.target.sl_i == (activeHandle.sl_i + 1)) || (e.target.sl_i == (activeHandle.sl_i - 1)))
                pos = e.target.sl_pos
            else return;
        }
        let newValue = pos * maxValue / sliderWidth;
        setHandlePos(activeHandle, newValue)
        if (cb) cb(handles.map(h => h.sl_value))
    })
    // line.addEventListener("click", (e) => {
    //     // if (!activeHandle) return; 
    //     activeHandle.sl_value = e.offsetX * maxValue / sliderWidth;
    //     setHandlePos(activeHandle)
    //     if (cb) cb(handles.map(h => h.sl_value))
    // })
    holder.addEventListener("mouseleave", (e) => {
        if (!activeHandle) return; 
        activeHandle.classList.remove("active")
        activeHandle = null
    })     
    window.addEventListener("resize", () => {
        newSliderWidth = host.offsetWidth
        if (newSliderWidth != sliderWidth) {
            sliderWidth = newSliderWidth
            handles.forEach(h => setHandlePos(h, h.sl_value, true))
        }
    })
    return { holder, line, handles, values, maxValue }
}