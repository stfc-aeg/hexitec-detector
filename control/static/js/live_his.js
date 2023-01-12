var liveview_enable = false;
var autosize_enableHis = false;
var size_sliderHis = null;
// const api_url = '/api/0.1/live_histogram/';
var img_scaling = 1.0;

let livehis_endpoint;

var LiveHisApp = (function()
{
    'use strict';

    var init = function() 
    {
        // Configure sizing range slider

        size_sliderHis = new Slider('#size_rangeHis').on("slideStop", changeSizeEventHis);
        !autosize_enableHis ? size_sliderHis.enable() : size_sliderHis.disable();

        // Start the update polling loop
        pollUpdateHis();

        // Resize the image to fit available GUI space
        autosize_enableHis = true;
        resizeHis();
        autosize_enableHis = false;
    };

    var pollUpdateHis = function()
    {
        if (liveview_enable) {
            updateHis();
        }
        setTimeout(pollUpdateHis, 100);
    };

    return {
        init: init,
    };

})();

document.addEventListener("DOMContentLoaded", function()
{
    livehis_endpoint = new AdapterEndpoint("live_histogram");

    LiveHisApp.init();
});

// Bind the window resize event
window.addEventListener('resize', function(event) {
    if (!liveview_enable) {
        resizeHis();
    }
}, true);

function changeLiveViewEnable() 
{
    liveview_enable = document.getElementById('live_view_radio1').checked;
}

function changeAutosizeHisEnable()
{
    autosize_enableHis = document.getElementById('autosizeHis_radio1').checked;
    // console.log("HIS: You clicked autosize !")
    !autosize_enableHis ? size_sliderHis.enable() : size_sliderHis.disable();
    resizeHis();
}

function changeSizeEventHis(size_event)
{
    // console.log("HIS changeSizeEventNEW size_event: " + size_event);
    var new_size = size_event;
    img_scaling = new_size / 100;
    resizeHis();
}

function updateHis()
{
    // console.log("live_hasten.JS: updateHis()!");
    var img_new = document.getElementById('livehis_image');
    var data_src = img_new.getAttribute('data-src');
    img_new.setAttribute("src",
        data_src + '?' + new Date().getTime()
    );
}

function resizeHis()
{
    var image_element = document.getElementById('livehis_image');
    var img_height = image_element.naturalHeight;
    var img_width = image_element.naturalWidth;

    if (autosize_enableHis) {

        const lv_container = document.getElementById('livehis_container');
        const cssObj = window.getComputedStyle(lv_container, null);

        const padding = cssObj.getPropertyValue("padding");
        // Turn "40px 15px" string into tokens
        const padding_tokens = padding.match(/\d+/g);
        // Multiply by 2 because padding on both sides
        const width_padding = padding_tokens[1] * 2;
        const height_padding = padding_tokens[0] * 2;

        const img_container_width = lv_container.offsetWidth - width_padding;
        const img_container_height = lv_container.offsetHeight - height_padding;
        // console.log("HIS container: " + img_container_width + " " + img_container_height);
        // console.log("lv_container: " + lv_container.offsetWidth + " " + lv_container.offsetHeight);
        // console.log("padding: " + width_padding + " " + height_padding);

        var width_scaling = Math.min(img_container_width / img_width, 1.0);
        var height_scaling = Math.min(img_container_height / img_height, 1.0);

        img_scaling = Math.min(width_scaling, height_scaling);
        size_sliderHis.setValue(Math.floor(img_scaling * 100));
    }
    // .QuerySelector returns a HTMLImageElement object
    document.querySelector('#livehis_image').width = Math.floor(img_scaling * img_width);
    document.querySelector('#livehis_image').height = Math.floor(img_scaling * img_height);
}

// function(a,b){var c,d,e,f=this[0],g=f&&f.attributes;if(void 0===a){if(this.length&&(e=O.get(f),1===f.nodeType&&!N.get(f,"hasDataAttrs"))){c=g.length;while(c--)g[c]&&(d=g[c].name,0===d.indexOf("data-")&&(d=n.camelCase(d.slice(5)),R(f,d,e[d])));N.set(f,"hasDataAttrs",!0)}return e}return"object"==typeof a?this.each(function(){O.set(this,a)}):K(this,function(b){var c,d;if(f&&void 0===b){if(c=O.get(f,a)||O.get(f,a.replace(Q,"-$&").toLowerCase()),void 0!==c)return c;if(d=n.camelCase(a),c=O.get(f,d),void 0!==c)return c;if(c=R(f,d,void 0),void 0!==c)return c}else d=n.camelCase(a),this.each(function(){var c=O.get(this,d);O.set(this,d,b),a.indexOf("-")>-1&&void 0!==c&&O.set(this,a,b)})},null,b,arguments.length>1,null,!0)} function
