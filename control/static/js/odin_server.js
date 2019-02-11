api_version = '0.1';

var api_url = '/api/' + api_version + '/';
var odin_data_url = api_url + 'hexitec/odin_data/';
// Vars added for Odin-Data
var reorder_enable = null;
var threshold_enable = null;
var charged_sharing_enable = null;
var addition_enable = null;
var discrimination_enable = null;
var next_frame_enable = null;
var calibration_enable = null;
var histogram_enable = null;

$( document ).ready(function()
{
    $('.dec-number').on('change', function () {
        const value = Number($(this).val());
        $(this).val(value.toFixed(2));
   });
   
    // update_api_version();
    // update_api_adapters();
    poll_update()
    
    $(".bootstrap-switch").bootstrapSwitch({
        'size': 'midi',
        'onSwitchChange': function(event, state) {

            var discriminate_enable = false;
            var addition_enable = false;
    
                // Do your logic in here according to the value 
            if ($(this).val() == "none")
            {
                console.log("Clicked on none");
            }
            if ($(this).val() == "add")
            {
                console.log("Clicked on add");
                addition_enable = true;
            }
            if ($(this).val() == "dis")
            {
                console.log("Clicked on dis");
                discriminate_enable = true;
            }
            var pixel_grid_size = $('#pixel-grid-size-text').prop('value');
            var charged_sharing_payload = {"charged_sharing": {"addition": addition_enable, "discrimination": discriminate_enable, "pixel_grid_size": parseInt(pixel_grid_size)} };

            $.ajax({
                type: "PUT",
                url: '/api/' + api_version + '/hexitec/odin_data',
                contentType: "application/json",
                data: JSON.stringify(charged_sharing_payload)
            });
        }
    })

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

});

function poll_update() {
/*    update_background_task(); */
    setTimeout(poll_update, 500);   
}

// function update_api_version() {

//     $.getJSON('/api', function(response) {
//         $('#api-version').html(response.api_version);
//         api_version = response.api_version;
//     });
// }

// function update_api_adapters() {

//     $.getJSON('/api/' + api_version + '/adapters/', function(response) {
//         adapter_list = response.adapters.join(", ");
//         $('#api-adapters').html(adapter_list);
//     });
// }

// function update_background_task() {

//     $.getJSON('/api/' + api_version + '/hexitec/background_task', function(response) {
//         var task_count = response.background_task.count;
//         var task_enabled = response.background_task.enable;
//         $('#task-count').html(task_count);
//         $('#task-enable').prop('checked', task_enabled);
//     });
// }

// // Development purposes only:
// function filename_button()
// {
//     var filename = $('#filename-text').prop('value');
//     console.log("filename_button(), Sample text contains: " + filename ); 

//     $.ajax({
//         type: "PUT",
//         url: '/api/' + api_version + `/hexitec/test_area`,
//         contentType: "application/json",
//         data: JSON.stringify({'target_text': filename })
//     });
//     /* Write filename to target_name's text field */
//     $('#target-name').html(filename);
// }

// function defaults_button()
// {
//     console.log("GOING TO LOAD data.json NOW !");
//     load_defaults_from_json();

// }

function reorder_rows_changed()
{
    var reorder_rows = $('#rows-text').prop('value');
    console.log("reorder_rows(), text is now: " + reorder_rows);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/reorder`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'height': parseInt(reorder_rows) }),
        success: function(result) {
            //console.log("Success");
            $('#rows-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#rows-warning').html(error);
        }
    });
}

function reorder_columns_changed()
{
    var reorder_columns = $('#columns-text').prop('value');
    console.log("reorder_columns(), text is now: " + reorder_columns); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/reorder`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'width': parseInt(reorder_columns) }),
        success: function(result) {
            //console.log("Success");
            $('#columns-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#columns-warning').html(error);
        }
    });
}

function threshold_filename_changed()
{
    var threshold_filename = $('#threshold-filename').prop('value');
    console.log("threshold_filename_changed(), is now: " + threshold_filename);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/threshold`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'threshold_filename': threshold_filename }),
        success: function(result) {
            //console.log("Success");
            $('#threshold-filename-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#threshold-filename-warning').html(error);
        }
    });
}

function threshold_value_changed()
{
    var threshold_value = $('#threshold-value').prop('value');
    console.log("threshold_value_changed(), is now: " + threshold_value);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/threshold`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'value': parseInt(threshold_value) }),
        success: function(result) {
            //console.log("Success");
            $('#threshold-value-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#threshold-value-warning').html(error);
        }

    });
}

function threshold_mode_changed(el)
{
    var threshold_mode = $('#threshold-mode').prop('value');

    if ((new RegExp("^None$").test(el.value) == true) || 
        (new RegExp("^Value$").test(el.value) == true) ||
        (new RegExp("^Filename$").test(el.value) == true))
    {
        // Correct choice, clear warning & send new choice
        $('#threshold-mode-warning').html("");

        $.ajax(`/api/` + api_version + `/hexitec/odin_data/threshold`, {
            method: "PUT",
            contentType: "application/json",
            data: JSON.stringify({'mode': threshold_mode })
        });
    } else {
        $('#threshold-mode-warning').html("Valid choices: None, Value, Filename");
    }
}

function gradients_filename_changed()
{
    var gradients_filename = $('#gradients-filename').prop('value');
    console.log("gradients_filename_changed(), is now: " + gradients_filename);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/calibration`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'gradients_filename': gradients_filename }),
        success: function(result) {
            //console.log("Success");
            $('#gradients-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#gradients-warning').html(error);
        }
    });
}

function intercepts_filename_changed()
{
    var intercepts_filename = $('#intercepts-filename').prop('value');
    console.log("intercepts_filename_changed(), is now: " + intercepts_filename);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/calibration`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'intercepts_filename': intercepts_filename }),
        success: function(result) {
            //console.log("Success");
            $('#intercepts-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#intercepts-warning').html(error);
        }
    });
}

function pixel_grid_size_changed()
{
    var pixel_grid_size = $('#pixel-grid-size-text').prop('value');
    console.log("pixel_grid_size(), text is now: " + pixel_grid_size); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/charged_sharing`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'pixel_grid_size': parseInt(pixel_grid_size) }),
        success: function(result) {
            //console.log("Success");
            $('#pixel-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#pixel-warning').html(error);
        }
    });
}

function max_frames_received_changed()
{
    var max_frames_received = $('#max-frames-received-text').prop('value');
    console.log("max_frames_received(), text is now: " + max_frames_received); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/histogram`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'max_frames_received': parseInt(max_frames_received) }),
        success: function(result) {
            //console.log("Success");
            $('#frames-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#frames-warning').html(error);
        }
    });
}

function bin_start_changed()
{
    var bin_start = $('#bin-start-text').prop('value');
    console.log("bin_start(), text is now: " + bin_start); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/histogram`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'bin_start': parseInt(bin_start) }),
        success: function(result) {
            //console.log("Success");
            $('#bin-start-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#bin-start-warning').html(error);
        }
    });
}

function bin_end_changed()
{
    var bin_end = $('#bin-end-text').prop('value');
    console.log("bin_end(), text is now: " + bin_end); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/histogram`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'bin_end': parseInt(bin_end) }),
        success: function(result) {
            //console.log("Success");
            $('#bin-end-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#bin-end-warning').html(error);
        }
    });
}

function bin_width_changed()
{
    var bin_width = parseFloat( $('#bin-width-text').prop('value'));

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/histogram`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'bin_width': bin_width }),
        success: function(result) {
            //console.log("Success");
            $('#bin-width-warning').html("");
        },
        error: function(request, msg, error) {
            console.log(request + " " + msg + " " + error);
            $('#bin-width-warning').html(error);
        }
    });
}

function loadJSON(path, callback) {
    console.log("path: " + path); 
    var xobj = new XMLHttpRequest();
        xobj.overrideMimeType("application/json");
    xobj.open('GET', path, true);
    xobj.onreadystatechange = function () {
          if (xobj.readyState == 4 && xobj.status == "200") {
            callback(xobj.responseText);
          }
    };
    console.log("xobj.status:" + xobj.status);
    xobj.send(null);  
 }

// function load_defaults_from_json() { 
//     console.log("load_defaults_from_json called");
//     var json;
//     loadJSON("data.json", function(response) {
//         json = JSON.parse(response);
//         console.log(json); // Successfully shows the result
//         // console.log("json.background_task.count: " + json.background_task.count);
//         // Read json values into variables..
//         reorder_enable = json.odin_data.reorder.enable;
//         threshold_enable = json.odin_data.threshold.enable;
//         // charged_sharing_enable = json.odin_data.;   // Redundant - no such API variable
//         // addition_enable = json.odin_data.charged_sharing.addition;
//         // discrimination_enable = json.odin_data.charged_sharing.discrimination;
//         next_frame_enable = json.odin_data.next_frame;
//         calibration_enable = json.odin_data.calibration.enable;
//         histogram_enable = json.odin_data.histogram.enable;
//         var reorder_rows = json.odin_data.reorder.height;
//         var reorder_columns = json.odin_data.reorder.width;
//         // Sanity Check: Write to console variables..
//         console.log("json.odin_data.reorder.enable: " + reorder_enable);
//         console.log(" threshold_enable: " + threshold_enable);
//         // console.log(" addition_enable: " + addition_enable);
//         // console.log(" discrimination_enable: " + discrimination_enable);
//         console.log(" next_frame_enable: " + next_frame_enable);
//         console.log(" calibration_enable: " + calibration_enable);
//         console.log(" histogram_enable: " + histogram_enable);
//         // Update UI checkboxes, API tree
//         // Update reorder enable..
//         updateReorderEnable(reorder_enable);
//         updateThresholdEnable(threshold_enable);
//         updateNextFrameEnable(next_frame_enable);
//         updateCalibrationEnable(calibration_enable);
//         updateHistogramEnable(histogram_enable);
//         updateReorderRows(reorder_rows);
        
//     });
//     // console.log("json is undefined here because var json out of scope now: " +json); // TypeError: json is undefined
// }


// Restricts input for each element in the set of matched elements to the given inputFilter.
(function($) {
    $.fn.inputFilter = function(inputFilter) {
        console.log("inputFilter()");
        return this.on("input keydown keyup mousedown mouseup select contextmenu drop", function() {
            if (inputFilter(this.value)) {
                this.oldValue = this.value;
                this.oldSelectionStart = this.selectionStart;
                this.oldSelectionEnd = this.selectionEnd;
            } else if (this.hasOwnProperty("oldValue")) {
                this.value = this.oldValue;
                this.setSelectionRange(this.oldSelectionStart, this.oldSelectionEnd);
            }
        });
    };
}(jQuery));
  
  
// Install input filters.
// Integers only:
$("#rows-text").inputFilter(function(value) {
    return /^-?\d*$/.test(value); });
$("#columns-text").inputFilter(function(value) {
    return /^-?\d*$/.test(value); });
$("#threshold-value").inputFilter(function(value) {
    return /^-?\d*$/.test(value); });
$("#max-frames-received-text").inputFilter(function(value) {
    return /^-?\d*$/.test(value); });
$("#bin-start-text").inputFilter(function(value) {
    return /^-?\d*$/.test(value); });
$("#bin-end-text").inputFilter(function(value) {
    return /^-?\d*$/.test(value); });

// Integers 3 or 5 only:
$("#pixel-grid-size-text").inputFilter(function(value) {
    return /^\d*$/.test(value) && (value === "" || parseInt(value) === 3 || parseInt(value) === 5); });

// Allowing floating type:
$("#bin-width-text").inputFilter(function(value) {
    return /^-?\d*[.,]?\d*$/.test(value); });
// $("#currencyTextBox").inputFilter(function(value) {
//     return /^-?\d*[.,]?\d{0,2}$/.test(value); });
// $("#uintTextBox").inputFilter(function(value) {
//     return /^\d*$/.test(value); });
// $("#hexTextBox").inputFilter(function(value) {
//     return /^[0-9a-f]*$/i.test(value); });


// Test migrating from live_view.js to here..

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


/// Experimental, utilised by load_defaults_from_json()
function updateReorderEnable(reorder_enable) {

    $.ajax({
        type: "PUT",
        url: odin_data_url + 'reorder',
        contentType: "application/json",
        data: JSON.stringify({"enable": reorder_enable})
    });
    // Aaaand, update reorder html element 
    // $('#reorderButton').prop('checked', reorder_enable);
    $("[name='reorder_enable']").bootstrapSwitch('state', reorder_enable, true);
};

function updateThresholdEnable(threshold_enable) {

    $.ajax({
        type: "PUT",
        url: odin_data_url + 'threshold',
        contentType: "application/json",
        data: JSON.stringify({"enable": threshold_enable})
    });
    $("[name='threshold_enable']").bootstrapSwitch('state', threshold_enable, true);
};

function updateNextFrameEnable(next_frame_enable) {

    $.ajax({
        type: "PUT",
        url: odin_data_url + 'next_frame',
        contentType: "application/json",
        data: JSON.stringify(next_frame_enable)
    });
    $("[name='next_frame_enable']").bootstrapSwitch('state', next_frame_enable, true);
};

function updateCalibrationEnable(calibration_enable) {

    $.ajax({
        type: "PUT",
        url: odin_data_url + 'calibration',
        contentType: "application/json",
        data: JSON.stringify({"enable": calibration_enable})
    });
    $("[name='calibration_enable']").bootstrapSwitch('state', calibration_enable, true);
};

function updateAdditionEnable(addition_enable) {

    $.ajax({
        type: "PUT",
        url: odin_data_url + 'charged_sharing',
        contentType: "application/json",
        data: JSON.stringify({"addition": addition_enable})
    });
    $("[name='addition_enable']").bootstrapSwitch('state', addition_enable, true);

};

function updateDiscriminationEnable(discrimination_enable) {

    $.ajax({
        type: "PUT",
        url: odin_data_url + 'charged_sharing',
        contentType: "application/json",
        data: JSON.stringify({"discrimination": discrimination_enable})
    });
    $("[name='discrimination_enable']").bootstrapSwitch('state', discrimination_enable, true);
};

function updateHistogramEnable(histogram_enable) {

    $.ajax({
        type: "PUT",
        url: odin_data_url + 'histogram',
        contentType: "application/json",
        data: JSON.stringify({"enable": histogram_enable})
    });
    $("[name='histogram_enable']").bootstrapSwitch('state', histogram_enable, true);
};

function updateReorderRows(reorder_rows) {
    
    $('#rows-text').prop('value')  = reorder_rows;

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/reorder`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'height': parseInt(reorder_rows) })
    });
};
