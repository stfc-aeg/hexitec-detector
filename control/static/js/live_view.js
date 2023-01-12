var liveview_enable = false;
var clip_enable = false;
var clip_slider = null;
var autosize_enable = false;
var size_slider = null;
// const api_url = '/api/0.1/live_view/';
var img_scaling = 1.0;

let liveview_endpoint;

var LiveViewApp = (function()
{
    'use strict';

    var init = function() 
    {
        // Configure clipping range slider

        clip_slider = new Slider('#clip_range').on("slideStop", changeClipEvent);

        // Configure sizing range slider

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

        // Resize the image to fit available GUI space
        autosize_enable = true;
        resizeImage();
        autosize_enable = false;
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
        // console.log("changeClipEvent: " + slide_event);
        changeClipRange(slide_event);
    };

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
    clip_enable = document.getElementById('clip_enable_radio1').checked;
    clip_enable ? clip_slider.enable() : clip_slider.disable();
    changeClipRange();
}

var changeClipRange = function(clip_range=null)
{
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

    // console.log('New range changed: min=' + clip_range[0] + " max=" + clip_range[1]);
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
    autosize_enable = document.getElementById('autosize_radio1').checked;
    // console.log("IMAGE You clicked autosize !")
    !autosize_enable ? size_slider.enable() : size_slider.disable();
    resizeImage();
}

function changeSizeEvent(size_event)
{
    // console.log("IMAGE changeSizeEventNEW size_event: " + size_event);
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
    // console.log("live_view.JS: updateImage() called!");
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
        // console.log("IMG container: " + img_container_width + " " + img_container_height);
        // console.log("lv_container: " + lv_container.offsetWidth + " " + lv_container.offsetHeight);
        // console.log("padding: " + width_padding + " " + height_padding);

        var width_scaling = Math.min(img_container_width / img_width, 1.0);
        var height_scaling = Math.min(img_container_height / img_height, 1.0);

        img_scaling = Math.min(width_scaling, height_scaling);
        size_slider.setValue(Math.floor(img_scaling * 100));
    }
    // console.log("width: " + Math.floor(img_scaling * img_width));
    // console.log("height: " + Math.floor(img_scaling * img_height));
    // .QuerySelector returns a HTMLImageElement object
    document.querySelector('#liveview_image').width = Math.floor(img_scaling * img_width);
    document.querySelector('#liveview_image').height = Math.floor(img_scaling * img_height);
}
