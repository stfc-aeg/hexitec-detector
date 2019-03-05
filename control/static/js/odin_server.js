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
var hdf_write_enable = null;

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

    // Configure hdf write switch
    $("[name='hdf_write_enable']").bootstrapSwitch({disabled:true});
    $("[name='hdf_write_enable']").bootstrapSwitch('state', hdf_write_enable, true);
    
    $('input[name="hdf_write_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeHdfWriteEnable();
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

function reorder_rows_changed()
{
    var reorder_rows = $('#rows-text').prop('value');
    console.log("reorder_rows(), text is now: " + reorder_rows);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/reorder`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'height': parseInt(reorder_rows) }),
        success: function(result) {
            $('#rows-warning').html("");
        },
        error: function(request, msg, error) {
            $('#rows-warning').html(error + ": " + request.responseText);
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
            $('#columns-warning').html("");
        },
        error: function(request, msg, error) {
            $('#columns-warning').html(error + ": " + request.responseText);
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
            $('#threshold-filename-warning').html("");
        },
        error: function(request, msg, error) {
            $('#threshold-filename-warning').html(error + ": " + request.responseText);
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
            $('#threshold-value-warning').html("");
        },
        error: function(request, msg, error) {
            $('#threshold-value-warning').html(error + ": " + request.responseText);
        }
    });
}

function threshold_mode_changed(el)
{
    var threshold_mode = $('#threshold-mode').prop('value');

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/threshold`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'mode': threshold_mode }),
        success: function(result) {
            $('#threshold-mode-warning').html("");
        },
        error: function(request, msg, error) {
            $('#threshold-mode-warning').html(error + ": " + request.responseText);
        }
    });
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
            $('#gradients-warning').html("");
        },
        error: function(request, msg, error) {
            $('#gradients-warning').html(error + ": " + request.responseText);
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
            $('#intercepts-warning').html("");
        },
        error: function(request, msg, error) {
            $('#intercepts-warning').html(error + ": " + request.responseText);
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
            $('#pixel-warning').html("");
        },
        error: function(request, msg, error) {
            $('#pixel-warning').html(error + ": " + request.responseText);
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
            $('#frames-warning').html("");
        },
        error: function(request, msg, error) {
            $('#frames-warning').html(error + ": " + request.responseText);
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
            $('#bin-start-warning').html("");
        },
        error: function(request, msg, error) {
            $('#bin-start-warning').html(error + ": " + request.responseText);
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
            $('#bin-end-warning').html("");
        },
        error: function(request, msg, error) {
            $('#bin-end-warning').html(error + ": " + request.responseText);
        }
    });
}

function bin_width_changed()
{
    var bin_width = parseFloat( $('#bin-width-text').prop('value'));
    console.log("bin_width: " + bin_width);
    $.ajax(`/api/` + api_version + `/hexitec/odin_data/histogram`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'bin_width': bin_width }),
        success: function(result) {
            $('#bin-width-warning').html("");
        },
        error: function(request, msg, error) {
            $('#bin-width-warning').html(error + ": " + request.responseText);
        }
    });
}

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

//// Odin Data Placeholder for now:

var changeHdfWriteEnable = function()
{
    hdf_write_enable = $("[name='hdf_write_enable']").bootstrapSwitch('state');
    console.log("Odin server, Odin Data.. hdf_write_enable? " + hdf_write_enable + "JSON: " + JSON.stringify(hdf_write_enable));
    $.ajax({
        type: "PUT",
        url: api_url + 'fp/config/hdf/write',
        contentType: "application/json",
        data: JSON.stringify(hdf_write_enable),
        success: function(result) {
            console.log("Success");
            $('#hdf-write-enable-warning').html("");
            // If write Enabled, must disable config files, file path and filename  (and vice versa)
            if (hdf_write_enable == true)
            {
                console.log("writing is true");
                $('#fr-config').prop('disabled', true);
                $('#fp-config').prop('disabled', true);
                $('#hdf-file-path').prop('disabled', true);
                $('#hdf-file-name').prop('disabled', true);
            }
            else
            {
                console.log("writing is false");
                $('#fr-config').prop('disabled', false);
                $('#fp-config').prop('disabled', false);
                $('#hdf-file-path').prop('disabled', false);
                $('#hdf-file-name').prop('disabled', false);
            }
        },
        error: function(request, msg, error) {
            // console.log("request: " + request + " msg: " + msg + " error: " + error);
            $('#hdf-write-enable-warning').html(error + ": " + request.responseText);
        }
    });
};

function fp_config_changed()
{
    var fp_config_file = $('#fp-config').prop('value');
    $.ajax({
        type: "PUT",
        url: api_url + 'fp/config/config_file',
        contentType: "application/json",
        data: fp_config_file,
        success: function(result) {
            $('#fp-config-warning').html("");
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', false);
        },
        error: function(request, msg, error) {
            $('#fp-config-warning').html(error + ": " + request.responseText);
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

function fr_config_changed()
{
    var fr_config_file = $('#fr-config').prop('value');
    $.ajax({
        type: "PUT",
        url: api_url + 'fr/config/config_file',
        contentType: "application/json",
        data: (fr_config_file),
        success: function(result) {
            $('#fr-config-warning').html("");
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', false);
        },
        error: function(request, msg, error) {
            $('#fr-config-warning').html(error + ": " + request.responseText);
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

//curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/fp/config/hdf/file/path -d "/tmp"
function hdf_file_path_changed()
{
    var hdf_file_path = $('#hdf-file-path').prop('value');
    $.ajax({
        type: "PUT",
        url: api_url + 'fp/config/hdf/file/path',
        contentType: "application/json",
        data: (hdf_file_path),
        success: function(result) {
            $('#hdf-file-path-warning').html("");
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', false);
        },
        error: function(request, msg, error) {
            $('#hdf-file-path-warning').html(error + ": " + request.responseText);
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

// curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/fp/config/hdf/file/name -d "test"
function hdf_file_name_changed()
{
    var hdf_file_name = $('#hdf-file-name').prop('value');
    $.ajax({
        type: "PUT",
        url: api_url + 'fp/config/hdf/file/name',
        contentType: "application/json",
        data: (hdf_file_name),
        success: function(result) {
            $('#hdf-file-name-warning').html("");
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', false);
        },
        error: function(request, msg, error) {
            $('#hdf-file-name-warning').html(error + ": " + request.responseText);
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};



