api_version = '0.1';

var api_url = '/api/' + api_version + '/';
var odin_data_url = api_url + 'hexitec/odin_data/';
// Vars added for Odin-Data
var reorder_enable = false;
var raw_data_enable = false;
var addition_enable = false;
var discrimination_enable = false;
var charged_sharing_enable = false; // Track state to ease logic inside apply_ui_values()
var next_frame_enable = false;
var calibration_enable = false;
var hdf_write_enable = false;

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

            // Assume cs/add/dis all false, Let if statements decide which one(s) are true
            charged_sharing_enable = false;
            addition_enable = false;
            discrimination_enable = false;

            if ($(this).val() == "add")
            {
                addition_enable = true;
                charged_sharing_enable = true;
            }
            if ($(this).val() == "dis")
            {
                discrimination_enable = true;
                charged_sharing_enable = true;
            }
            var pixel_grid_size = $('#pixel-grid-size-text').prop('value');

            var addition_payload = {"addition": 
                                {"enable": addition_enable,
                                "pixel_grid_size": parseInt(pixel_grid_size)} };

            var discrimination_payload = {"discrimination": 
                                {"enable": discrimination_enable, 
                                "pixel_grid_size": parseInt(pixel_grid_size)} };

            // ODIN paramTree
            $.ajax({
                type: "PUT",
                url: '/api/' + api_version + '/hexitec/odin_data',
                contentType: "application/json",
                data: JSON.stringify(addition_payload),
                success: function(result) {
                    console.log("Successfully updated Addition settings in odin_data");
                },
                error: function(request, msg, error) {
                    console.log("FAILED to update Addition settings in odin_data: " + error);
                }
            });

            // ODIN paramTree
            $.ajax({
                type: "PUT",
                url: '/api/' + api_version + '/hexitec/odin_data',
                contentType: "application/json",
                data: JSON.stringify(discrimination_payload),
                success: function(result) {
                    console.log("Successfully updated Discrimination settings in odin_data");
                },
                error: function(request, msg, error) {
                    console.log("FAILED to update Discrimination settings in odin_data: " + error);
                }
            });

            // plugin param
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config',
                contentType: "application/json",
                data: JSON.stringify(addition_payload),
                success: function(result) {
                    console.log("Successfully updated Addition plugin settings");
                },
                error: function(request, msg, error) {
                    console.log("FAILED to update Addition plugin settings: " + error);
                }
            });

            // plugin param
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config',
                contentType: "application/json",
                data: JSON.stringify(discrimination_payload),
                success: function(result) {
                    console.log("Successfully updated Discrimination plugin settings");
                },
                error: function(request, msg, error) {
                    console.log("FAILED to update Discrimination plugin settings: " + error);
                }
            });
        }
    })


    /// Style checkbox(es) into a ON/OFF slider

    // Configure Reorder switch
    $("[name='reorder_enable']").bootstrapSwitch();
    $("[name='reorder_enable']").bootstrapSwitch('state', reorder_enable, true);
    $('input[name="reorder_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeReorderEnable();
    });

    // Configure Raw Data switch
    $("[name='raw_data_enable']").bootstrapSwitch();
    $("[name='raw_data_enable']").bootstrapSwitch('state', raw_data_enable, true);
    $('input[name="raw_data_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeRawDataEnable();
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

    // Configure hdf write switch
    $("[name='hdf_write_enable']").bootstrapSwitch({disabled:true});
    $("[name='hdf_write_enable']").bootstrapSwitch('state', hdf_write_enable, true);
    $('input[name="hdf_write_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeHdfWriteEnable();
    });

    // Buttons for loading sequence config files, Applying settings

    $('#storeButton').on('click', function(event) {
        // Load the 12 different sequence files
        store_sequence_files();
    });

    $('#applyButton').on('click', function(event) {
        apply_ui_values();
    });


    // Test button:
    $('#executeButton').on('click', function(event) {
        var execute_file_1 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_1.json";
        $.ajax({
            type: "PUT",
            url: api_url + 'hexitec/fp/config/config_file',
            contentType: "application/json",
            data: execute_file_1,
            success: function(result) {
                $('#fp-config-warning').html("");
                $("[name='hdf_write_enable']").bootstrapSwitch('disabled', false);
            },
            error: function(request, msg, error) {
                $('#fp-config-warning').html(error + ": " + format_error_message(request.responseText));
                $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
            }
        });
    });

    // Odin Control

    $('#connectButton').on('click', function(event) {
        // Connect with hardware
        // function_to_be_created();
        console.log("Clicked on connect button");
        connect_hardware();
    });

    $('#initialiseButton').on('click', function(event) {
        // Initialise hardware
        // function_to_be_created();
        console.log("Clicked on initialise");
        initialise_hardware();
    });

    $('#acquireButton').on('click', function(event) {
        // Acquire data from camera
        // function_to_be_created();
        console.log("Click on acquire button");
        collect_data();
    });

    $('#disconnectButton').on('click', function(event) {
        // Disconnect with hardware
        // function_to_be_created();
        console.log("Clicked on disconnect button");
        disconnect_hardware();
    });

});

// curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/odin_data/adapter_settings/hexitec_fem/
// -d '{"connect_hardware": ""}' | python -m json.tool
function connect_hardware() {

    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/odin_data/adapter_settings/hexitec_fem/',
        contentType: "application/json",
        data: JSON.stringify({"connect_hardware": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function initialise_hardware() {

    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/odin_data/adapter_settings/hexitec_fem/',
        contentType: "application/json",
        data: JSON.stringify({"initialise_hardware": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function collect_data() {

    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/odin_data/adapter_settings/hexitec_fem/',
        contentType: "application/json",
        data: JSON.stringify({"collect_data": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function disconnect_hardware() {

    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/odin_data/adapter_settings/hexitec_fem/',
        contentType: "application/json",
        data: JSON.stringify({"disconnect_hardware": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function store_sequence_files() {

    // Hardcoded paths are bad but no way around it here: (Move this away from the install folder !)
    var sequence_file_1 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_1.json";
    var sequence_file_2 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_2.json";
    var sequence_file_3 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_3.json";
    var sequence_file_4 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_4.json";
    var sequence_file_5 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_5.json";
    var sequence_file_6 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_6.json";
    var sequence_file_7 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_7.json";
    var sequence_file_8 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_8.json";
    var sequence_file_9 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_9.json";
    var sequence_file_10 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_10.json";
    var sequence_file_11 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_11.json";
    var sequence_file_12 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/store_sequence_12.json";

    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_1);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_2);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_3);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_4);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_5);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_6);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_7);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_8);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_9);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_10);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_11);
    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_12);

}

// send_sequence_file: Used to store or execute the sequence of plugin(s)
//  defined by (a json) file
function send_sequence_file(path, file) {

    $.ajax({
        type: "PUT",
        url: path,
        contentType: "application/json",
        data: file,
        success: function(result) {
            console.log("Successfully loaded configuration file: " + file);
        },
        error: function(request, msg, error) {
            console.log("Failed to load configuration file: " + file);
        }
    });
}

// apply_ui_values: Disconnect existing sequence of plugins, 
//  load the sequence of plugins corresponding to UI settings
function apply_ui_values() {

    // Hardcoded paths are bad but no way around it here: (Move this away from the install folder ?!)
    var sequence_file_1 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_1.json";
    var sequence_file_2 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_2.json";
    var sequence_file_3 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_3.json";
    var sequence_file_4 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_4.json";
    var sequence_file_5 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_5.json";
    var sequence_file_6 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_6.json";
    var sequence_file_7 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_7.json";
    var sequence_file_8 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_8.json";
    var sequence_file_9 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_9.json";
    var sequence_file_10 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_10.json";
    var sequence_file_11 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_11.json";
    var sequence_file_12 =  "/u/ckd27546/develop/projects/odin-demo/install/config/data/client_msgs/execute_sequence_12.json";
    
    // Start by loading (executing) the corresponding JSON config file
    //   (disconnects currently connected plugins, connects up selected plugins)
    if (next_frame_enable == true) 
    {
        if (calibration_enable  == true) 
        {
            // Next = true, calibration = true
            if (charged_sharing_enable == true)
            {
                // Next = true, calibration = true, CS = true
                // Is CS Addition or Discrimination?
                if (addition_enable == true)
                {
                    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_8);
                }
                if (discrimination_enable == true)
                {
                    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_12);
                }
            }
            else
            {
                // next = true, calibration = true CS = false
                send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_4);
            }
        }
        else
        {
            // next = true, calibration = false
            if (charged_sharing_enable == true)
            {
                // next = true, calib = false, cs == true
                // Is CS Addition or Discrimination?
                if (addition_enable == true)
                {
                    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_6);
                }
                if (discrimination_enable == true)
                {
                    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_10);
                }
            }
            else
            {
                // next = true, calib = false, cs = false
                send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_2);
            }
        }
    }
    else    // next_frame not selected
    {
        if (calibration_enable == true)
        {
            // Next = false, Calibration = true
            if (charged_sharing_enable == true)
            {
                // Next = false, calibration = true, CS = true
                // Is CS Addition or Discrimination?
                if (addition_enable == true)
                {
                    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_7);
                }
                if (discrimination_enable == true)
                {
                    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_11);
                }
            }
            else
            {
                // next = false calibration = true, CS = false
                send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_3);
            }
        }
        else    // next_frame, calibration not selected
        {
            if (charged_sharing_enable == true) 
            {
                // Next = false, calibration = false, CS = true
                // CS is Addition or Discrimination?
                if (addition_enable == true)
                {
                    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_5);
                }
                if (discrimination_enable == true)
                {
                    send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_9);
                }
            }
            else
            {
                // next = False, calibration = False, charged_sharing = False
                send_sequence_file(api_url + 'hexitec/fp/config/config_file', sequence_file_1);
            }
        }
    }

    // Load all UI settings into corresponding plugins
    changeReorderEnable();
    changeRawDataEnable();
    reorder_rows_changed();
    reorder_columns_changed();

    var threshold_mode = $('#threshold-mode-text').prop('value');
    // Check whether threshold filename mode requested
    //  (0 if strings equal, 1 if they're different)
    if (threshold_mode.localeCompare("filename") == 0)
    {
        threshold_filename_changed();
    }
    threshold_value_changed();
    threshold_mode_changed();

    gradients_filename_changed();
    intercepts_filename_changed();
    pixel_grid_size_changed();
    max_frames_received_changed();
    bin_start_changed();
    bin_end_changed();
    bin_width_changed();

    // Don't (re-)load FP config file from UI or config may be changed unintentionally
    // fp_config_changed(); 
    hdf_file_path_changed();
    hdf_file_name_changed();
    hdf_frames_changed();

    // If hdf write already enabled, toggle off and on so hdf settings sent
    if ( $("[name='hdf_write_enable']").prop('checked') == true)
    {
        console.log("THIS IS VEERY TRUE");
        setTimeout(setHdfWrite(false), 400);
        setTimeout(setHdfWrite(true), 800);
    }
    else
    {
        console.log("THIS IS VERY FALSE");
    }
}


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
    reorder_rows = JSON.stringify(parseInt(reorder_rows));
    // Each plugin has a height parameter, must update all seven
    $.ajax(api_url + `hexitec/odin_data/reorder/height`, {
        method: "PUT",
        contentType: "application/json",
        data: reorder_rows,
        success: function(result) {
            $('#rows-warning').html("");
            update_plugin_value("addition", "height", reorder_rows);
            update_plugin_value("calibration", "height", reorder_rows);
            update_plugin_value("discrimination", "height", reorder_rows);
            update_plugin_value("histogram", "height", reorder_rows);
            update_plugin_value("next_frame", "height", reorder_rows);
            update_plugin_value("reorder", "height", reorder_rows);
            update_plugin_value("threshold", "height", reorder_rows);
        },
        error: function(request, msg, error) {
            $('#rows-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function reorder_columns_changed()
{
    var reorder_columns = $('#columns-text').prop('value');
    reorder_columns = JSON.stringify(parseInt(reorder_columns));
    // Each plugin has a width parameter, must update all seven
    $.ajax(api_url + `hexitec/odin_data/reorder/width`, {
        method: "PUT",
        contentType: "application/json",
        data: reorder_columns,
        success: function(result) {
            $('#columns-warning').html("");
            update_plugin_value("addition", "width", reorder_columns);
            update_plugin_value("calibration", "width", reorder_columns);
            update_plugin_value("discrimination", "width", reorder_columns);
            update_plugin_value("histogram", "width", reorder_columns);
            update_plugin_value("next_frame", "width", reorder_columns);
            update_plugin_value("reorder", "width", reorder_columns);
            update_plugin_value("threshold", "width", reorder_columns);
        },
        error: function(request, msg, error) {
            $('#columns-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

// update_plugin_value: Helps reorder_rows_changed(),
//  reorder_columns_changed() to set a plugin's key's value
function update_plugin_value(plugin, key, value)
{
    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/fp/config/' + plugin + '/' + key,
        contentType: "application/json",
        data: value,
    });
}

function threshold_filename_changed()
{
    var threshold_filename = $('#threshold-filename-text').prop('value');
    threshold_filename = JSON.stringify(threshold_filename);

    $.ajax(api_url + `hexitec/odin_data/threshold/threshold_filename`, {
        method: "PUT",
        contentType: "application/json",
        data: threshold_filename,
        success: function(result) {
            $('#threshold-filename-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/threshold/threshold_filename',
                contentType: "application/json",
                data: threshold_filename,
                success: function(result) {
                    console.log("threshold_filename  ACCEPTED");
                    $('#threshold-filename-warning').html("");
                },
                error: function(request, msg, error) {
                    console.log("threshold_filename REJECTED");
                    $('#threshold-filename-warning').html(error + ": " + format_error_message(request.responseText));
                }
            });
        },
        error: function(request, msg, error) {
            $('#threshold-filename-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function threshold_value_changed()
{
    var threshold_value = $('#threshold-value-text').prop('value');
    threshold_value = JSON.stringify(parseInt(threshold_value));

    $.ajax(api_url + `hexitec/odin_data/threshold/threshold_value`, {
        method: "PUT",
        contentType: "application/json",
        data: threshold_value,
        success: function(result) {
            $('#threshold-value-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/threshold/threshold_value',
                contentType: "application/json",
                data: threshold_value,
            });
        },
        error: function(request, msg, error) {
            $('#threshold-value-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function threshold_mode_changed()
{
    var threshold_mode = $('#threshold-mode-text').prop('value');
    threshold_mode = JSON.stringify(threshold_mode);

    $.ajax(api_url + `hexitec/odin_data/threshold/threshold_mode`, {
        method: "PUT",
        contentType: "application/json",
        data: threshold_mode,
        success: function(result) {
            $('#threshold-mode-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/threshold/threshold_mode',
                contentType: "application/json",
                data: threshold_mode,
            });
        },
        error: function(request, msg, error) {
            $('#threshold-mode-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function gradients_filename_changed()
{
    var gradients_filename = $('#gradients-filename-text').prop('value');
    gradients_filename = JSON.stringify(gradients_filename);

    $.ajax(api_url + `hexitec/odin_data/calibration/gradients_filename`, {
        method: "PUT",
        contentType: "application/json",
        data: gradients_filename,
        success: function(result) {
            $('#gradients-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/calibration/gradients_filename',
                contentType: "application/json",
                data: gradients_filename,
                success: function(result) {
                    $('#gradients-filename-warning').html("");
                },
                error: function(request, msg, error) {
                    $('#gradients-filename-warning').html(error + ": " + format_error_message(request.responseText));
                }
            });
        },
        error: function(request, msg, error) {
            $('#gradients-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function intercepts_filename_changed()
{
    var intercepts_filename = $('#intercepts-filename-text').prop('value');
    intercepts_filename = JSON.stringify(intercepts_filename);

    $.ajax(api_url + `hexitec/odin_data/calibration/intercepts_filename`, {
        method: "PUT",
        contentType: "application/json",
        data: intercepts_filename,
        success: function(result) {
            $('#intercepts-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/calibration/intercepts_filename',
                contentType: "application/json",
                data: intercepts_filename,
                success: function(result) {
                    $('#intercepts-filename-warning').html("");
                },
                error: function(request, msg, error) {
                    $('#intercepts-filename-warning').html(error + ": " + format_error_message(request.responseText));
                }
            });
        },
        error: function(request, msg, error) {
            $('#intercepts-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

// pixel_grid_size_changed: Both Addition and Discrimination have this setting,
//  need to update both as Odin current cannot reliably tell us which plugin is loaded
function pixel_grid_size_changed()
{
    var pixel_grid_size = $('#pixel-grid-size-text').prop('value');
    pixel_grid_size = JSON.stringify(parseInt( pixel_grid_size));

    // Targeting HexitecAdditionPlugin
    $.ajax(api_url + `hexitec/odin_data/addition/pixel_grid_size`, {
        method: "PUT",
        contentType: "application/json",
        data: pixel_grid_size,
        success: function(result) {
            $('#pixel-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/addition/pixel_grid_size',
                contentType: "application/json",
                data: pixel_grid_size,
            });
        },
        error: function(request, msg, error) {
            $('#pixel-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });

    // Targeting HexitecDiscriminationPlugin
    $.ajax(api_url + `hexitec/odin_data/discrimination/pixel_grid_size`, {
        method: "PUT",
        contentType: "application/json",
        data: pixel_grid_size,
        success: function(result) {
            $('#pixel-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/discrimination/pixel_grid_size',
                contentType: "application/json",
                data: pixel_grid_size,
            });
        },
        error: function(request, msg, error) {
            $('#pixel-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

// max_frames_received_changed: Sets number of frames processed before histograms written to disk
function max_frames_received_changed()
{
    var max_frames_received = $('#max-frames-received-text').prop('value');
    max_frames_received = JSON.stringify(parseInt(max_frames_received));

    $.ajax(api_url + `hexitec/odin_data/histogram/max_frames_received`, {
        method: "PUT",
        contentType: "application/json",
        data: max_frames_received,
        success: function(result) {
            $('#frames-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/histogram/max_frames_received',
                contentType: "application/json",
                data: max_frames_received,
            });
        },
        error: function(request, msg, error) {
            $('#frames-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function bin_start_changed()
{
    var bin_start = $('#bin-start-text').prop('value');
    bin_start = JSON.stringify(parseInt(bin_start));

    $.ajax(api_url + `hexitec/odin_data/histogram/bin_start`, {
        method: "PUT",
        contentType: "application/json",
        data: bin_start,
        success: function(result) {
            $('#bin-start-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/histogram/bin_start',
                contentType: "application/json",
                data: bin_start,
            });
        },
        error: function(request, msg, error) {
            $('#bin-start-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function bin_end_changed()
{
    var bin_end = $('#bin-end-text').prop('value');
    bin_end = JSON.stringify(parseInt(bin_end));

    $.ajax(api_url + `hexitec/odin_data/histogram/bin_end`, {
        method: "PUT",
        contentType: "application/json",
        data: bin_end,
        success: function(result) {
            $('#bin-end-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/histogram/bin_end',
                contentType: "application/json",
                data: bin_end,
            });
        },
        error: function(request, msg, error) {
            $('#bin-end-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function bin_width_changed()
{
    var bin_width = $('#bin-width-text').prop('value');
    bin_width = JSON.stringify(parseFloat(bin_width));

    $.ajax(api_url + `hexitec/odin_data/histogram/bin_width`, {
        method: "PUT",
        contentType: "application/json",
        data: bin_width,
        success: function(result) {
            $('#bin-width-warning').html("");
            $.ajax({
                type: "PUT",
                url: api_url + 'hexitec/fp/config/histogram/bin_width',
                contentType: "application/json",
                data: bin_width,
            });
        },
        error: function(request, msg, error) {
            $('#bin-width-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

var changeReorderEnable = function()
{
    reorder_enable = $("[name='reorder_enable']").bootstrapSwitch('state');
    // Write straight into HexitecReorderPlugin's variable
    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/fp/config/reorder/reorder',
        contentType: "application/json",
        data: JSON.stringify(reorder_enable),
        success: function(result) {
            console.log("Reorder successfully changed");
        },
        error: function(request, msg, error) {
            console.log("Reorder couldn't be changed");
        }
    });
};

var changeRawDataEnable = function ()
{
    raw_data_enable = $("[name='raw_data_enable']").bootstrapSwitch('state');
    // Write straight into HexitecReorderPlugin's variable
    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/fp/config/reorder/raw_data',
        contentType: "application/json",
        data: JSON.stringify(raw_data_enable),
        success: function(result) {
            console.log("Raw_data successfully changed");
        },
        error: function(request, msg, error) {
            console.log("Raw_data couldn't be changed");
        }
    });
};

var changeNextFrameEnable = function()
{
    next_frame_enable = $("[name='next_frame_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: odin_data_url + 'next_frame',
        contentType: "application/json",
        data: JSON.stringify(next_frame_enable)
    });
};

var changeCalibrationEnable = function()
{
    calibration_enable = $("[name='calibration_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: odin_data_url + 'calibration',
        contentType: "application/json",
        data: JSON.stringify({"enable": calibration_enable})
    });
};

var changeNextFrameEnable = function()
{
    next_frame_enable = $("[name='next_frame_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: odin_data_url + 'next_frame',
        contentType: "application/json",
        data: JSON.stringify(next_frame_enable)
    });
};

var changeCalibrationEnable = function()
{
    calibration_enable = $("[name='calibration_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: odin_data_url + 'calibration',
        contentType: "application/json",
        data: JSON.stringify({"enable": calibration_enable})
    });
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
    console.log("changeDiscrm called");
    $.ajax({
        type: "PUT",
        url: odin_data_url + 'charged_sharing',
        contentType: "application/json",
        data: JSON.stringify({"discrimination": discrimination_enable})
    });
};

var changeHdfWriteEnable = function()
{
    hdf_write_enable = $("[name='hdf_write_enable']").bootstrapSwitch('state');
    setHdfWrite(hdf_write_enable);
};

var selectChange = function(selected)
{
    // curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/odin_data/adapter_settings -d '{"sensors_layout": "5x5"}' | python -m json.tool

    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/odin_data/adapter_settings',
        contentType: "application/json",
        data: JSON.stringify({"sensors_layout": selected}),
        success: function(result) {
            $('#sensors-layout-warning').html("");
        },
        error: function(request, msg, error) {
            $('#sensors-layout-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

// setHdfWrite: Helper function to toggle hdf writing on/off
function setHdfWrite(enable)
{
    hdf_write_enable = enable;
    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/fp/config/hdf/write',
        contentType: "application/json",
        data: JSON.stringify(hdf_write_enable),
        success: function(result) {
            $('#hdf-write-enable-warning').html("");
            // If write Enabled, must disable access to config files, 
            //  file path & name, frames (and vice versa)
            if (hdf_write_enable == true)
            {
                console.log("writing is true");
                $('#fr-config').prop('disabled', true);
                $('#fp-config-text').prop('disabled', true);
                $('#hdf-file-path-text').prop('disabled', true);
                $('#hdf-file-name-text').prop('disabled', true);
                $('#hdf-frames-text').prop('disabled', true);
            }
            else
            {
                console.log("writing is false");
                $('#fr-config').prop('disabled', false);
                $('#fp-config-text').prop('disabled', false);
                $('#hdf-file-path-text').prop('disabled', false);
                $('#hdf-file-name-text').prop('disabled', false);
                $('#hdf-frames-text').prop('disabled', false);
            }
        },
        error: function(request, msg, error) {
            $('#hdf-write-enable-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

// format_error_message: Help format Error message before displayed in UI
function format_error_message(error) {
    // Error messages typically look like: 
    //  "error": "File name must not be empty"
    var withoutQuotation = error.replace(/"/g,'');
    var withoutBrackets = withoutQuotation.replace('{', '').replace('}', '');
    return withoutBrackets.replace('error: ','');
}

function fp_config_changed()
{
    var fp_config_file = $('#fp-config-text').prop('value');
    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/fp/config/config_file',
        contentType: "application/json",
        data: fp_config_file,
        success: function(result) {
            $('#fp-config-warning').html("");
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', false);
        },
        error: function(request, msg, error) {
            $('#fp-config-warning').html(error + ": " + format_error_message(request.responseText));
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
            $('#fr-config-warning').html(error + ": " + format_error_message(request.responseText));
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

//curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fp/config/hdf/file/path -d "/tmp"
function hdf_file_path_changed()
{
    var hdf_file_path = $('#hdf-file-path-text').prop('value');
    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/fp/config/hdf/file/path',
        contentType: "application/json",
        data: (hdf_file_path),
        success: function(result) {
            $('#hdf-file-path-warning').html("");
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', false);
        },
        error: function(request, msg, error) {
            $('#hdf-file-path-warning').html(error + ": " + format_error_message(request.responseText));
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

// curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fp/config/hdf/file/name -d "test"
function hdf_file_name_changed()
{
    var hdf_file_name = $('#hdf-file-name-text').prop('value');
    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/fp/config/hdf/file/name',
        contentType: "application/json",
        data: (hdf_file_name),
        success: function(result) {
            $('#hdf-file-name-warning').html("");
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', false);
        },
        error: function(request, msg, error) {
            $('#hdf-file-name-warning').html(error + ": " + format_error_message(request.responseText));
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

// curl  -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fp/config/hdf/frames -d "3"
function hdf_frames_changed()
{
    var hdf_frames = $('#hdf-frames-text').prop('value');
    $.ajax({
        type: "PUT",
        url: api_url + 'hexitec/fp/config/hdf/frames',
        contentType: "application/json",
        data: (hdf_frames),
        success: function(result) {
            $('#hdf-frames-warning').html("");
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', false);
        },
        error: function(request, msg, error) {
            $('#hdf-frames-warning').html(error + ": " + format_error_message(request.responseText));
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

