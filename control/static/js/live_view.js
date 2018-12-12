var LiveViewApp = (function()
{
    'use strict';

    var liveview_enable = false;
    var clip_enable = false;
    var autosize_enable = false;
    var clip_slider = null;
    var size_slider = null;
    var api_url = '/api/0.1/';    //'/api/0.1/live_view/';
    var live_view_url = api_url + 'live_view/';
    var odin_data_url = api_url + 'hexitec/odin_data/';
    var img_elem = null;
    var img_scaling = 1.0;
    // Vars added for Odin-Data
    var reorder_enable = true;
    var height_rows = 80;
    var width_columns = 80;
    var threshold_enable = false;
    var charged_sharing_enable = false;
    var addition_enable = false;
    var discrimination_enable = false;
    var next_frame_enable = false;
    var calibration_enable = false;
    var histogram_enable = false;
    var test_put = false;
    var test_get = false;
    
    var init = function() 
    {
        // $('.radio1').on('switch-change', function () {
        //     $('.radio1').bootstrapSwitch('toggleRadioState');
        // });
        // // or
        // $('.radio1').on('switch-change', function () {
        //     $('.radio1').bootstrapSwitch('toggleRadioStateAllowUncheck');
        // });
        // // or
        // $('.radio1').on('switch-change', function () {
        //     $('.radio1').bootstrapSwitch('toggleRadioStateAllowUncheck', false);
        // });
    

        // Get reference to image element and attch the resize function to its onLoad event
        img_elem = $('#liveview_image');
        img_elem.load(function() 
        {
            resizeImage();
        });

        /// Style checkbox(s) into a ON/OFF slider

        // Configure Reorder switch
        $("[name='reorder_enable']").bootstrapSwitch();
        $("[name='reorder_enable']").bootstrapSwitch('state', reorder_enable, true);
        $('input[name="reorder_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeReorderEnable();
        });

        // Configure Threshold switch
        $("[name='threshold_enable']").bootstrapSwitch();
        $("[name='threshold_enable']").bootstrapSwitch('state', threshold_enable, true);
        $('input[name="threshold_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeThresholdEnable();
        });

        // Configure Charged Sharing switch
        $("[name='charged_sharing_enable']").bootstrapSwitch();
        $("[name='charged_sharing_enable']").bootstrapSwitch('state', charged_sharing_enable, true);
        $('input[name="charged_sharing_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeChargedSharingEnable();
        });

        // Configure Addition switch
        $("[name='addition_enable']").bootstrapSwitch();
        $("[name='addition_enable']").bootstrapSwitch('state', addition_enable, true);
        $('input[name="addition_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeAdditionEnable();
        });

        // Configure Charged Sharing switch
        $("[name='discrimination_enable']").bootstrapSwitch();
        $("[name='discrimination_enable']").bootstrapSwitch('state', discrimination_enable, true);
        $('input[name="discrimination_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeDiscriminationEnable();
        });

        // Configure Next Frame switch
        $("[name='next_frame_enable']").bootstrapSwitch();
        $("[name='next_frame_enable']").bootstrapSwitch('state', next_frame_enable, true);
        $('input[name="next_frame_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeNextFrameEnable();
        });

        // Configure Calibration switch
        $("[name='calibration_enable']").bootstrapSwitch();
        $("[name='calibration_enable']").bootstrapSwitch('state', calibration_enable, true);
        $('input[name="calibration_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeCalibrationEnable();
        });

        // Configure Histogram switch
        $("[name='histogram_enable']").bootstrapSwitch();
        $("[name='histogram_enable']").bootstrapSwitch('state', histogram_enable, true);
        $('input[name="histogram_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeHistogramEnable();
        });

        // testPut function..
        $("[name='test_put']").bootstrapSwitch();
        $("[name='test_put']").bootstrapSwitch('state', test_put, true);
        $('input[name="test_put"]').on('switchChange.bootstrapSwitch', function(event,state) {
            testPut();
        });

        // testGet function..
        $("[name='test_get']").bootstrapSwitch();
        $("[name='test_get']").bootstrapSwitch('state', test_get, true);
        $('input[name="test_get"]').on('switchChange.bootstrapSwitch', function(event,state) {
            testGet();
        });

        ///

        // Configure auto-update switch
        $("[name='liveview_enable']").bootstrapSwitch();
        $("[name='liveview_enable']").bootstrapSwitch('state', liveview_enable, true);
        $('input[name="liveview_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeLiveViewEnable();
        });

        // Configure clipping enable switch
        $("[name='clip_enable']").bootstrapSwitch();
        $("[name='clip_enable']").bootstrapSwitch('state', clip_enable, true);
        $('input[name="clip_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeClipEnable();
        });

        // Configure clipping range slider
        clip_slider = $("#clip_range").slider({}).on('slideStop', changeClipEvent);

        // Configure autosizing enable switch
        $("[name='autosize_enable']").bootstrapSwitch();
        $("[name='autosize_enable']").bootstrapSwitch('state', autosize_enable, true);
        $('input[name="autosize_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
            changeAutosizeEnable();
        });

        // Configure sizing range slider
        size_slider = $("#size_range").slider({}).on('slideStop', changeSizeEvent);
        size_slider.slider(!autosize_enable ? "enable" : "disable");

        // Retrieve API data and populate controls
        $.getJSON(live_view_url, function (response)
        {
            buildColormapSelect(response.colormap_selected, response.colormap_options);
            updateClipRange(response.data_min_max, true);
            changeClipEnable();
        });

        // Bind the window resize event
        $( window ).on('resize', function()
        {
            if (!liveview_enable) {
                resizeImage();
            }
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

    var buildColormapSelect = function(selected_colormap, colormap_options)
    {
        let dropdown = $('#colormap_select');

        dropdown.empty();

        var colormaps_sorted = Object.keys(colormap_options).sort();

        $.each(colormaps_sorted, function(idx, colormap) {
            var colormap_name = colormap_options[colormap];
            var selected = '';
            if (colormap.localeCompare(selected_colormap) === 0)
            {
                selected = 'selected="true"'
            }
            dropdown.append('<option ' + selected + 
                ' value=' + colormap + '>' + colormap_name + '</option>');
        });

        dropdown.change(function()
        {
            changeColormap(this.value);
        });
    };

    var changeLiveViewEnable = function() 
    {
        liveview_enable = $("[name='liveview_enable']").bootstrapSwitch('state');
    };

    // Needed this in addition to the corresponding definition in init()
    //  $("[name='htmls_named_func']").bootstrapSwitch();
    var changeReorderEnable = function()
    {
        reorder_enable = $("[name='reorder_enable']").bootstrapSwitch('state');
        $.ajax({
            type: "PUT",
            url: odin_data_url + 'reorder',
            contentType: "application/json",
            data: JSON.stringify({"enable": reorder_enable})
        });
    };

    var changeThresholdEnable = function()
    {
        threshold_enable = $("[name='threshold_enable']").bootstrapSwitch('state');
        $.ajax({
            type: "PUT",
            url: odin_data_url + 'threshold',
            contentType: "application/json",
            data: JSON.stringify({"enable": threshold_enable})
        });
        console.log("threshold: " + threshold_enable);
    };

    var changeNextFrameEnable = function()
    {
        next_frame_enable = $("[name='next_frame_enable']").bootstrapSwitch('state');
        console.log("next_frame_enable: " + next_frame_enable);
        $.ajax({
            type: "PUT",
            url: odin_data_url + 'next_frame',
            contentType: "application/json",
            data: JSON.stringify(next_frame_enable)
        });
        console.log("next frame: " + next_frame_enable);
    };

    var testPut = function()
    {
        console.log("Testing PUT -> config/hdf/file/path = ...");
        $.ajax({
            type: "PUT",
            url: 'config/hdf/file',
            // url: '/api/0.1/hexitec/odin_data/' + 'reorder', // Correct path..
            // url: 'hdf/file',
            contentType: "application/json",
            data: JSON.stringify({"path": "/path/to/file.txt"})
        });
    };

    var testGet = function()
    {
        console.log("testGet()..");
        // $.getJSON('/api/' + api_version + '/hexitec/background_task', function(response) {
        $.getJSON('config/hdf/file', function(response) {
        // $.getJSON('hdf/file', function(response) {   // FrameProcessorapp:458
            // var path = response.file.path;
            // var task_enabled = response.background_task.enable;
            console.log("Hiya");
            // console.log(task_enabled);
        });
    };

    var changeCalibrationEnable = function()
    {
        calibration_enable = $("[name='calibration_enable']").bootstrapSwitch('state');
        console.log("calibration_enable: " + calibration_enable);
        $.ajax({
            type: "PUT",
            url: odin_data_url + 'calibration',
            contentType: "application/json",
            data: JSON.stringify({"enable": calibration_enable})
        });
        console.log("calibration: " + calibration_enable);
    };

    var changeChargedSharingEnable = function()
    {
        console.log("using name: " + $("[name='charged_sharing_enable']").bootstrapSwitch('state'));
        console.log("using id: " + $("[id='charged_sharing_enable']").prop('state'));
        
        /* Don't need to set anything specifically in the API for this
            since either one of Addition/Discrimination is true or
            neither (the former means CS is enabled, latter CS disabled) 
        */
        // charged_sharing_enable = $("[name='charged_sharing_enable']").bootstrapSwitch('state');
        // $.ajax({
        //     type: "PUT",
        //     url: odin_data_url + 'charged_sharing',
        //     contentType: "application/json",
        //     data: JSON.stringify({"enable": charged_sharing_enable})
        // });
    };

    var changeAdditionEnable = function()
    {
        addition_enable = $("[name='addition_enable']").bootstrapSwitch('state');
        $.ajax({
            type: "PUT",
            url: odin_data_url + 'charged_sharing',
            contentType: "application/json",
            data: JSON.stringify({"addition": addition_enable})
        });
    };

    var changeDiscriminationEnable = function()
    {
        discrimination_enable = $("[name='discrimination_enable']").bootstrapSwitch('state');
        $.ajax({
            type: "PUT",
            url: odin_data_url + 'charged_sharing',
            contentType: "application/json",
            data: JSON.stringify({"discrimination": discrimination_enable})
        });
    };

    var changeHistogramEnable = function()
    {
        histogram_enable = $("[name='histogram_enable']").bootstrapSwitch('state');
        console.log("histogram_enable: " + histogram_enable);
        $.ajax({
            type: "PUT",
            url: odin_data_url + 'histogram',
            contentType: "application/json",
            data: JSON.stringify({"enable": histogram_enable})
        });
        console.log("histogram: " + histogram_enable);
    };

    var updateClipRange = function(data_min_max, reset_current=false)
    {
        var data_min = parseInt(data_min_max[0]);
        var data_max = parseInt(data_min_max[1]);

        $('#clip_min').text(data_min);
        $('#clip_max').text(data_max);

        var current_values = clip_slider.data('slider').getValue();

        if (reset_current) {
            current_values = [data_min, data_max]
        }

        clip_slider.slider('setAttribute', 'max', data_max);
        clip_slider.slider('setAttribute', 'min', data_min);
        clip_slider.slider('setValue', current_values);

    };

    var changeClipEnable = function()
    {
        clip_enable = $("[name='clip_enable']").bootstrapSwitch('state');
        clip_slider.slider(clip_enable ? "enable" : "disable");
        changeClipRange();
    };

    var changeClipEvent = function(slide_event)
    {
        var new_range = slide_event.value;
        changeClipRange(new_range);
    };

    var changeClipRange = function(clip_range=null) {
        
        if (clip_range === null)
        {
            clip_range = [
                clip_slider.slider('getAttribute', 'min'),
                clip_slider.slider('getAttribute', 'max')
            ]
        }
        if (!clip_enable)
        {
            clip_range = [null, null]
        }

        console.log('Clip range changed: min=' + clip_range[0] + " max=" + clip_range[1]);
        $.ajax({
            type: "PUT",
            url: live_view_url,
            contentType: "application/json",
            data: JSON.stringify({"clip_range": clip_range})
        });

    };

    var changeAutosizeEnable = function()
    {
        autosize_enable = $("[name='autosize_enable']").bootstrapSwitch('state');
        size_slider.slider(!autosize_enable ? "enable" : "disable");
        resizeImage();
    };

    var changeSizeEvent = function(size_event)
    {
        var new_size = size_event.value;
        img_scaling = new_size / 100;
        console.log("CHANGED img_scaling to " + img_scaling);
        resizeImage();
    };

    var changeColormap = function(value)
    {
        console.log("Colormap changed to " + value)
        $.ajax({
            type: "PUT",
            url: live_view_url,
            contentType: "application/json",
            data: '{"colormap_selected": "' + value +'" }'
        });
        updateImage();
    }

    var updateImage = function()
    {
        img_elem.attr("src", img_elem.attr("data-src") + '?' +  new Date().getTime());

        $.getJSON(live_view_url + "data_min_max", function(response)
        {
            updateClipRange(response.data_min_max, !clip_enable);
        });
    };

    var resizeImage = function()
    {

        var img_width = img_elem.naturalWidth();
        var img_height = img_elem.naturalHeight();

        if (autosize_enable) {

            var img_container_width =  $("#liveview_container").width();
            var img_container_height = $("#liveview_container").height();

            var width_scaling = Math.min(img_container_width / img_width, 1.0);
            var height_scaling = Math.min(img_container_height / img_height, 1.0);

            img_scaling = Math.min(width_scaling, height_scaling);
            size_slider.data('slider').setValue(Math.floor(img_scaling * 100));
        }

        img_elem.width( Math.floor(img_scaling * img_width));
        img_elem.height(Math.floor(img_scaling * img_height));

    };

    return {
        init: init,
    };

})();

$( document ).ready(function() 
{
    LiveViewApp.init();
});

// Generate naturalWidth/naturalHeight methods for images in JQuery
(function($){
    var
    props = ['Width', 'Height'],
    prop;

    while (prop = props.pop()) {
        (function (natural, prop) {
            $.fn[natural] = (natural in new Image()) ?
            function () {
                return this[0][natural];
            } :
            function () {
                var
                node = this[0],
                img,
                value;

                if (node.tagName.toLowerCase() === 'img') {
                    img = new Image();
                    img.src = node.src,
                    value = img[prop];
                }
                return value;
            };
        }('natural' + prop, prop.toLowerCase()));
    }
}(jQuery));

