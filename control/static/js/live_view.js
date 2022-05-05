var liveview_enable = false;
var clip_enable = false;
var clip_slider = null;
var autosize_enable = false;
var size_slider = null;
const api_url = '/api/0.1/live_view/';
var img_scaling = 1.0;

let liveview_endpoint;

var LiveViewApp = (function()
{
    'use strict';

    var init = function() 
    {
        // Configure clipping range slider

        // /// Old implementation utilising jQuery
        // clip_slider = $("#clip_range").slider({}).on('slideStop', changeClipEvent);
        // // console.log("Old,clip_slider: " + clip_slider + " " + typeof clip_slider);

        clip_slider = new Slider('#clip_range').on("slideStop", changeClipEvent);

        // // Configure sizing range slider
        // size_slider = $("#size_range").slider({}).on('slideStop', changeSizeEvent);
        // size_slider.slider(!autosize_enable ? "enable" : "disable");

        size_slider = new Slider('#size_range').on("slideStop", changeSizeEvent);
        !autosize_enable ? size_slider.enable() : size_slider.disable();

        liveview_endpoint.get('')
        .then(result => {
            // console.log(result);
            // console.log("clip_slider: " + clip_slider + " " + typeof clip_slider);
            buildColormapSelect(result.colormap_selected, result.colormap_options);
            updateClipRange(result.data_min_max, true);
            changeClipEnable();
        })
        .catch(error => {
            console.log("Failed to populate controls: " + error.message);
        });

        // Start the update polling loop
        pollUpdate();
    };

    var pollUpdate = function()
    {
        if (liveview_enable) {
            updateImage();
        }
        setTimeout(pollUpdate, 100);
    };

    var changeClipEvent = function(slide_event)
    {
        console.log("changeClipEvent: " + slide_event);
        changeClipRange(slide_event);
    };

    // var changeClipEventNEW = function(slide_event)
    // {
    //     console.log("changeClipEventNEW: " + slide_event);
    //     changeClipRangeNEW(slide_event);
    // };

    return {
        init: init,
    };

})();

document.addEventListener("DOMContentLoaded", function()
{
    liveview_endpoint = new AdapterEndpoint("live_view");

    LiveViewApp.init();
});

// Bind the window resize event
window.addEventListener('resize', function(event) {
    if (!liveview_enable) {
        resizeImage();
    }
}, true);

var buildColormapSelect = function(selected_colormap, colormap_options)
{
    let dropdown = document.getElementById("colormap_select");
    dropdown.innerHTML += "";

    var colormaps_sorted = Object.keys(colormap_options).sort();

    colormaps_sorted.forEach((colormap, idx) => {
        var colormap_name = colormap_options[colormap];
        var selected = '';
        if (colormap.localeCompare(selected_colormap) === 0)
        {
            selected = 'selected="true"'
        }
        dropdown.innerHTML += '<option ' + selected + ' value=' + colormap + '>' + colormap_name + '</option>';
    });

    // let select = document.querySelector("#colormap_select");
    dropdown.addEventListener("change", (e) => {
        changeColormap(dropdown.value);
    });
};

function changeLiveViewEnable() 
{
    liveview_enable = document.getElementById('live_view_radio1').checked;
}

var updateClipRange = function(data_min_max, reset_current=false)
{
//     var data_min = parseInt(data_min_max[0]);
//     var data_max = parseInt(data_min_max[1]);

//     $('#clip_min').text(data_min);
//     $('#clip_max').text(data_max);

//     var current_values = clip_slider.data('slider').getValue();

//     if (reset_current) {
//         current_values = [data_min, data_max]
//     }
//     clip_slider.slider('setAttribute', 'max', data_max);
//     clip_slider.slider('setAttribute', 'min', data_min);
//     clip_slider.slider('setValue', current_values);
// }

// var updateClipRangeNEW = function(data_min_max, reset_current=false)
// {
    var data_min = parseInt(data_min_max[0]);
    var data_max = parseInt(data_min_max[1]);

    document.querySelector('#clip_min').innerHTML = data_min;
    document.querySelector('#clip_max').innerHTML = data_max;

    var current_values = clip_slider.getValue();

    if (reset_current) {
        current_values = [data_min, data_max]
    }

    clip_slider.setAttribute('max', data_max);
    clip_slider.setAttribute('min', data_min);
    clip_slider.setValue(current_values);
}

function changeClipEnable()
{
//     clip_enable = document.getElementById('clip_enable_radio1').checked;
//     clip_slider.slider(clip_enable ? "enable" : "disable");
//     changeClipRange();
// }

// // Largely ornamental, contents of this function to go into the above (changeClipEnable() function)
// function changeClipEnableNEW()
// {
//     console.log("changeClipEnableNEW - Largely just pretending");
    clip_enable = document.getElementById('clip_enable_radio1').checked;
    clip_enable ? clip_slider.enable() : clip_slider.disable();
    // clip_slider.slider(clip_enable ? "enable" : "disable");
    changeClipRange();
}

var changeClipRange = function(clip_range=null) {

//     if (clip_range === null)
//     {
//         clip_range = [
//             clip_slider.slider('getAttribute', 'min'),
//             clip_slider.slider('getAttribute', 'max')
//         ]
//     }
//     if (!clip_enable)
//     {
//         clip_range = [null, null]
//     }

//     console.log('Clip range changed: min=' + clip_range[0] + " max=" + clip_range[1]);
//     liveview_endpoint.put({"clip_range": clip_range}, '')
//     .then(result => {
//         // console.log("changeClipRange updated Successful");
//     })
//     .catch(error => {
//         console.log("changeClipRange failed: " + error.message);
//     });
// }

// var changeClipRangeNEW = function(clip_range=null) {

    if (clip_range === null)
    {
        clip_range = [
            clip_slider.getAttribute('min'),
            clip_slider.getAttribute('max')
        ]
    }
    if (!clip_enable)
    {
        clip_range = [null, null]
    }

    console.log('New range changed: min=' + clip_range[0] + " max=" + clip_range[1]);
    liveview_endpoint.put({"clip_range": clip_range}, '')
    .then(result => {
        // console.log("changeClipRange updated Successful");
    })
    .catch(error => {
        console.log("changeClipRangeNEW failed: " + error.message);
    });
}

function changeAutosizeEnable()
{
//     autosize_enable = document.getElementById('autosize_radio1').checked;

//     size_slider.slider(!autosize_enable ? "enable" : "disable");
//     resizeImage();
// }

// function changeAutosizeEnableNEW()  /// Contents of this to largely replace contents of above function
// {
    autosize_enable = document.getElementById('autosize_radio1').checked;
    // console.log("You clicked autosize !")
    !autosize_enable ? size_slider.enable() : size_slider.disable();
    resizeImage();
}

function changeSizeEvent(size_event)
{
//     console.log("changeSizeEvent size_event: " + size_event + " " + size_event.value);
//     var new_size = size_event.value;
//     img_scaling = new_size / 100;
//     resizeImage();
// }

// function changeSizeEventNEW(size_event)
// {
    console.log("changeSizeEventNEW size_event: " + size_event);
    var new_size = size_event;
    img_scaling = new_size / 100;
    resizeImage();
}

function changeColormap(value)
{
    liveview_endpoint.put({"colormap_selected": value}, '')
    .then(result => {
        // console.log("changeColormap updated Successful");
    })
    .catch(error => {
        console.log("changeColormap failed: " + error.message);
    });
    updateImage();
}

function updateImage()
{
    var img_new = document.getElementById('liveview_image');
    var data_src = img_new.getAttribute('data-src');
    img_new.setAttribute("src",
        data_src + '?' + new Date().getTime()
    );

    liveview_endpoint.get('')
    .then(result => {
        updateClipRange(result.data_min_max, !clip_enable);
    })
    .catch(error => {
        console.log("updateImage() failed: " + error.message);
    });
}

function resizeImage()
{
    var image_element = document.getElementById('liveview_image');
    var img_height = image_element.naturalHeight;
    var img_width = image_element.naturalWidth;

    if (autosize_enable) {

        const lv_container = document.getElementById('liveview_container');
        const cssObj = window.getComputedStyle(lv_container, null);

        const padding = cssObj.getPropertyValue("padding");
        // Turn "40px 15px" string into tokens
        const padding_tokens = padding.match(/\d+/g);
        // Multiply by 2 because padding on both sides
        const width_padding = padding_tokens[1] * 2;
        const height_padding = padding_tokens[0] * 2;

        const img_container_width = lv_container.offsetWidth - width_padding;
        const img_container_height = lv_container.offsetHeight - height_padding;
        // console.log("container_width: " + img_container_width + " = " + lv_container.offsetWidth + " - " + width_padding);
        // console.log("container_height: " + img_container_height + " = " + lv_container.offsetHeight + " - " + height_padding);

        var width_scaling = Math.min(img_container_width / img_width, 1.0);
        var height_scaling = Math.min(img_container_height / img_height, 1.0);
        // console.log("width_scaling: " + width_scaling + " = Math.min(" + img_container_width + " / " + img_width + ", 1.0) i.e. = Math.min( = " + (img_container_width / img_width) + ", 1.0)");
        // console.log("height_scaling: " + height_scaling + " = Math.min(" + img_container_height + " / " + img_height + ", 1.0) i.e. = Math.min( = " + (img_container_height / img_height) + ", 1.0)");

        img_scaling = Math.min(width_scaling, height_scaling);
        // size_slider.data('slider').setValue(Math.floor(img_scaling * 100));
        size_slider.setValue(Math.floor(img_scaling * 100));
    }
    // .QuerySelector returns a HTMLImageElement object
    document.querySelector('#liveview_image').width = Math.floor(img_scaling * img_width);
    document.querySelector('#liveview_image').height = Math.floor(img_scaling * img_height)
}

// function(a,b){var c,d,e,f=this[0],g=f&&f.attributes;if(void 0===a){if(this.length&&(e=O.get(f),1===f.nodeType&&!N.get(f,"hasDataAttrs"))){c=g.length;while(c--)g[c]&&(d=g[c].name,0===d.indexOf("data-")&&(d=n.camelCase(d.slice(5)),R(f,d,e[d])));N.set(f,"hasDataAttrs",!0)}return e}return"object"==typeof a?this.each(function(){O.set(this,a)}):K(this,function(b){var c,d;if(f&&void 0===b){if(c=O.get(f,a)||O.get(f,a.replace(Q,"-$&").toLowerCase()),void 0!==c)return c;if(d=n.camelCase(a),c=O.get(f,d),void 0!==c)return c;if(c=R(f,d,void 0),void 0!==c)return c}else d=n.camelCase(a),this.each(function(){var c=O.get(this,d);O.set(this,d,b),a.indexOf("-")>-1&&void 0!==c&&O.set(this,a,b)})},null,b,arguments.length>1,null,!0)} function
