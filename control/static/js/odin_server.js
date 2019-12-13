api_version = '0.1';
var hexitec_url = '/api/' + api_version + '/hexitec/';

// Vars added for Odin-Data
var raw_data_enable = false;
var addition_enable = false;
var discrimination_enable = false;
var charged_sharing_enable = false; // Track state to ease logic inside apply_ui_values()
var next_frame_enable = false;
var calibration_enable = false;
var hdf_write_enable = false;

var base_path = "/u/ckd27546/develop/projects/odin-demo/hexitec-detector/data/config/"
var store_filename = "store_sequence_";
var execute_filename = "execute_sequence_";
var sensors_layout   = "2x2";

var polling_thread_running = false;
var system_health = true;
var fem_error_id = -1;
// var dark_correction_enable = false;

$( document ).ready(function()
{
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

            // plugin param
            $.ajax({
                type: "PUT",
                url: hexitec_url + 'detector/daq/config',
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
                url: hexitec_url + 'detector/daq/config',
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
    $('#testButton').on('click', function(event) {

        test_iac();
        ;
    });

    // Odin Control

    // Configure Dark Correction switch
    // $("[name='dark_correction_enable']").bootstrapSwitch();
    // $("[name='dark_correction_enable']").bootstrapSwitch('state', dark_correction_enable, true);
    // $('input[name="dark_correction_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
    //     changeDarkCorrectionEnable();
    // });

    $('#connectButton').on('click', function(event) {
 
        connect_hardware();
        if (polling_thread_running == false)
        {
            polling_thread_running = true;
            start_polling_thread();
        }
    });

    $('#initialiseButton').on('click', function(event) {
 
        initialise_hardware();
    });

    $('#acquireButton').on('click', function(event) {
 
        collect_data();
    });

    $('#disconnectButton').on('click', function(event) {
 
        disconnect_hardware();
        // Stop polling thread after a 2 second delay to 
        //  allow any lingering message(s) through
        setTimeout(function() {
            polling_thread_running = false;    
        }, 2000);
    });

    $('#offsetsButton').on('click', function(event) {

        collect_offsets();
    });

    
});

function collect_offsets() {

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
        contentType: "application/json",
        data: JSON.stringify({"collect_offsets": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

// Functions supporting polling..
function start_polling_thread() {

    poll_fem();
}

function poll_fem() {

    $.getJSON(hexitec_url + 'detector/', function(response) {

        var fems = response["detector"]["fems"]
        var adapter_status = response["detector"]["status"]

        var percentage_complete = fems["fem_0"]["operation_percentage_complete"];

        // http://localhost:8888/api/0.1/hexitec/detector/fems/fem_0/diagnostics/successful_reads
        // Diagnostics:
        var num_reads = fems["fem_0"]["diagnostics"]["successful_reads"];
        console.log("percentage_complete: " + fems["fem_0"]["operation_percentage_complete"] + " reads: " + num_reads + " msg: " + adapter_status["status_message"]);

        // Obtain overall adapter statuses

        var status_message = adapter_status["status_message"];
        $('#odin-control-message').html(status_message);

        // Get adapter error (either set or empty)
        var status_error = adapter_status["status_error"];
        // Include fem_id if adapter in error
        var status = "";
        if (status_error.length > 0)
        {
            status = "Fem: " + adapter_status["fem_id"] + " caused: '" + status_error + "'";
        }
        $('#odin-control-error').html(status);

        for (fem in fems)
        {
            //TODO: Prevent multiple fems overwriting one another's values

            // Hardcoded reading out all sensor data from one Fem:
            $('#vsr1_humidity').html(fems[fem]["vsr1_sensors"]["humidity"].toFixed(2));
            $('#vsr1_ambient').html(fems[fem]["vsr1_sensors"]["ambient"].toFixed(2));
            $('#vsr1_asic1').html(fems[fem]["vsr1_sensors"]["asic1"].toFixed(2));
            $('#vsr1_asic2').html(fems[fem]["vsr1_sensors"]["asic2"].toFixed(2));
            $('#vsr1_adc').html(fems[fem]["vsr1_sensors"]["adc"].toFixed(2));

            $('#vsr2_humidity').html(fems[fem]["vsr2_sensors"]["humidity"].toFixed(2));
            $('#vsr2_ambient').html(fems[fem]["vsr2_sensors"]["ambient"].toFixed(2));
            $('#vsr2_asic1').html(fems[fem]["vsr2_sensors"]["asic1"].toFixed(2));
            $('#vsr2_asic2').html(fems[fem]["vsr2_sensors"]["asic2"].toFixed(2));
            $('#vsr2_adc').html(fems[fem]["vsr2_sensors"]["adc"].toFixed(2));

            // console.log("fem: " + JSON.stringify(fems[fem]));   // e.g. fem = "fem_0"
            // fem: {"dark_correction":0,"ip_addr":"192.168.0.122","vsr2_sensors":{"humidity":12,
            //      "asic2":160,"asic1":46.25,"adc":47.5,"ambient":38.63902832031249},"status_error":"",
            //      "vsr1_sensors":{"humidity":12,"asic2":45.125,"asic1":44.9375,"adc":47.3125,
            //      "ambient":39.861689453124995},"port":"8070","read_sensors":null,
            //      "operation_percentage_complete":100,"health":true,"number_frames":10,"debug":false,
            //      "status_message":"Camera disconnected","id":0,"initialise_progress":0}

            // console.log("fem id: '" + fems[fem]["id"] + "' health: '" + fems[fem]["health"] + "' stat msg: '" + fems[fem]["status_message"] + "'.");
            
        }

        // system_health    // true=all fem(s) OK, false=fem(s) bad, fem_error_id says which one
        // fem_error_id

        // var status_message = response.fem_0.status_message;
        // var status_message = fems["fem_0"]["status_message"];
        // $('#odin-control-message').html(status_message);

        // // var status_error = response.fem_0.status_error;
        // var status_error = fems["fem_0"]["status_error"];
        // $('#odin-control-error').html(status_error);

        // var status = " msg: '" + status_message + "'";
        // if (status_error.length > 0)
        // {
        //     status = status + " error: '" + status_error + "'";
        // }
        // console.log(status);

        lampDOM = document.getElementById("Green");

        // Clear status if camera disconnected, otherwise look for any error
        if (status_message == "Camera disconnected")
        {
            // console.log("disconnected");
            lampDOM.classList.remove("lampGreen");
            lampDOM.classList.remove("lampRed");
        }
        else
        {
            // console.log("ELSE..");
            if (status_error.length  == 0)
            {
                // console.log("NO ERROR");
                lampDOM.classList.add("lampGreen");
            }
            else
            {
                // console.log("ERROR !!!1!");
                lampDOM.classList.remove("lampGreen");
                lampDOM.classList.add("lampRed");
            }
        }

        var progress_element = document.getElementById("progress-odin");
        progress_element.value = percentage_complete;

        if (polling_thread_running == true)
        {
            window.setTimeout(poll_fem, 950);
        }
        else
        {
            console.log("Stopping the polling thread");
        }
    });
}

// Test purposes only:
function test_iac() {

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
        contentType: "application/json",
        data: JSON.stringify({"commit_configuration": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}


// curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/detector/ -d '{"connect_hardware": ""}' | python -m json.tool
function connect_hardware() {

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
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
        url: hexitec_url + 'detector',
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
    console.log("CHANGED ACQUIRE BUTTON TO TARGET ADAPTER: 'start_acq' INSTEAD OF collect_data");
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/acquisition',
        contentType: "application/json",
        // data: JSON.stringify({"collect_data": ""}),
        data: JSON.stringify({"start_acq": ""}),
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
        url: hexitec_url + 'detector',
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

// curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/detector -d 
//  '{"commit_configuration": ""}' | python -m json.tool

function commit_configuration() {

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
        contentType: "application/json",
        data: JSON.stringify({"commit_configuration": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function store_sequence_files() {

    // Hardcoded paths are bad but no way around it here:
    var sequence_file_1 =  base_path + store_filename + "1_" + sensors_layout + ".json";
    var sequence_file_2 =  base_path + store_filename + "2_" + sensors_layout + ".json";
    var sequence_file_3 =  base_path + store_filename + "3_" + sensors_layout + ".json";
    var sequence_file_4 =  base_path + store_filename + "4_" + sensors_layout + ".json";
    var sequence_file_5 =  base_path + store_filename + "5_" + sensors_layout + ".json";
    var sequence_file_6 =  base_path + store_filename + "6_" + sensors_layout + ".json";
    var sequence_file_7 =  base_path + store_filename + "7_" + sensors_layout + ".json";
    var sequence_file_8 =  base_path + store_filename + "8_" + sensors_layout + ".json";
    var sequence_file_9 =  base_path + store_filename + "9_" + sensors_layout + ".json";
    var sequence_file_10 =  base_path + store_filename + "10_" + sensors_layout + ".json";
    var sequence_file_11 =  base_path + store_filename + "11_" + sensors_layout + ".json";
    var sequence_file_12 =  base_path + store_filename + "12_" + sensors_layout + ".json";

    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_1);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_2);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_3);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_4);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_5);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_6);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_7);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_8);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_9);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_10);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_11);
    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_12);
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
            ;
        },
        error: function(request, msg, error) {
            console.log("Failed to load configuration file: " + file);
        }
    });
}

// apply_ui_values: Disconnect existing sequence of plugins, 
//  load the sequence of plugins corresponding to UI settings
function apply_ui_values() {

    // Hardcoded paths are bad but no way around it here:
    var sequence_file_1 =  base_path + execute_filename + "1.json";
    var sequence_file_2 =  base_path + execute_filename + "2.json";
    var sequence_file_3 =  base_path + execute_filename + "3.json";
    var sequence_file_4 =  base_path + execute_filename + "4.json";
    var sequence_file_5 =  base_path + execute_filename + "5.json";
    var sequence_file_6 =  base_path + execute_filename + "6.json";
    var sequence_file_7 =  base_path + execute_filename + "7.json";
    var sequence_file_8 =  base_path + execute_filename + "8.json";
    var sequence_file_9 =  base_path + execute_filename + "9.json";
    var sequence_file_10 =  base_path + execute_filename + "10.json";
    var sequence_file_11 =  base_path + execute_filename + "11.json";
    var sequence_file_12 =  base_path + execute_filename + "12.json";
    
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
                    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_8);
                }
                if (discrimination_enable == true)
                {
                    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_12);
                }
            }
            else
            {
                // next = true, calibration = true CS = false
                send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_4);
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
                    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_6);
                }
                if (discrimination_enable == true)
                {
                    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_10);
                }
            }
            else
            {
                // next = true, calib = false, cs = false
                send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_2);
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
                    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_7);
                }
                if (discrimination_enable == true)
                {
                    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_11);
                }
            }
            else
            {
                // next = false calibration = true, CS = false
                send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_3);
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
                    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_5);
                }
                if (discrimination_enable == true)
                {
                    send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_9);
                }
            }
            else
            {
                // next = False, calibration = False, charged_sharing = False
                send_sequence_file(hexitec_url + 'fp/config/config_file', sequence_file_1);
            }
        }
    }

    // Load all UI settings into HexitecDAQ's ParameterTree
    changeRawDataEnable();

    threshold_mode_changed();
    threshold_value_changed();
    var threshold_mode = $('#threshold-mode-text').prop('value');
    // Update threshold filename if threshold filename mode set
    //  (0: strings equal [filename mode], 1: not [none/value mode])
    if (threshold_mode.localeCompare("filename") == 0)
    {
        threshold_filename_changed();
    }
    
    gradients_filename_changed();
    intercepts_filename_changed();
    pixel_grid_size_changed();
    bin_start_changed();
    bin_end_changed();
    bin_width_changed();

    hdf_file_path_changed();
    hdf_file_name_changed();

    // TODO: Redundant while file writing is controlled through the GUI (may change in the future???)
    // If hdf write already enabled, toggle off and on so hdf settings sent
    if ( $("[name='hdf_write_enable']").prop('checked') == true)
    {
        setTimeout(setHdfWrite(false), 400);
        setTimeout(setHdfWrite(true), 800);
    }

    // Experimental: Use commit_configuration to push ParameterTree settings to FP's plugins
    commit_configuration();
}


function poll_update() {
/*    update_background_task(); */
    setTimeout(poll_update, 500);   
}

function threshold_filename_changed()
{
    var threshold_filename = $('#threshold-filename-text').prop('value');
    threshold_filename = JSON.stringify(threshold_filename);

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/threshold/threshold_filename',
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
}

function threshold_value_changed()
{
    var threshold_value = $('#threshold-value-text').prop('value');
    threshold_value = JSON.stringify(parseInt(threshold_value));

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/threshold/threshold_value',
        contentType: "application/json",
        data: threshold_value,
        success: function(result) {
            $('#threshold-value-warning').html("");
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

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/threshold/threshold_mode',
        contentType: "application/json",
        data: threshold_mode,
        success: function(result) {
            $('#threshold-mode-warning').html("");
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

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/calibration/gradients_filename',
        contentType: "application/json",
        data: gradients_filename,
        success: function(result) {
            $('#gradients-filename-warning').html("");
        },
        error: function(request, msg, error) {
            $('#gradients-filename-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function intercepts_filename_changed()
{
    var intercepts_filename = $('#intercepts-filename-text').prop('value');
    intercepts_filename = JSON.stringify(intercepts_filename);

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/calibration/intercepts_filename',
        contentType: "application/json",
        data: intercepts_filename,
        success: function(result) {
            $('#intercepts-filename-warning').html("");
        },
        error: function(request, msg, error) {
            $('#intercepts-filename-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

// pixel_grid_size_changed: Both Addition and Discrimination have this setting,
//  need to update both as Odin current cannot reliably tell us which plugin is loaded
function pixel_grid_size_changed()
{
    var pixel_grid_size = $('#pixel-grid-size-text').prop('value');
    pixel_grid_size = JSON.stringify(parseInt( pixel_grid_size));

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/addition/pixel_grid_size',
        contentType: "application/json",
        data: pixel_grid_size,
        success: function(result) {
            $('#pixel-grid-size-warning').html("");
        },
        error: function(request, msg, error) {
            $('#pixel-grid-size-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/discrimination/pixel_grid_size',
        contentType: "application/json",
        data: pixel_grid_size,
        success: function(result) {
            $('#pixel-grid-size-warning').html("");
        },
        error: function(request, msg, error) {
            $('#pixel-grid-size-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

function bin_start_changed()
{
    var bin_start = $('#bin-start-text').prop('value');
    bin_start = JSON.stringify(parseInt(bin_start));

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/histogram/bin_start',
        contentType: "application/json",
        data: bin_start,
        success: function(result) {
            $('#bin-start-warning').html("");
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

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/histogram/bin_end',
        contentType: "application/json",
        data: bin_end,
        success: function(result) {
            $('#bin-end-warning').html("");
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

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/histogram/bin_width',
        contentType: "application/json",
        data: bin_width,
        success: function(result) {
            $('#bin-width-warning').html("");
        },
        error: function(request, msg, error) {
            $('#bin-width-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

// curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/detector/daq/config/reorder/raw_data -d "true"
// curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fp/config/reorder/raw_data -d "true"
var changeRawDataEnable = function ()
{
    raw_data_enable = $("[name='raw_data_enable']").bootstrapSwitch('state');
    
    $.ajax({
        type: "PUT",
        // TODO: Temporarily fixed until bool Type supported:
        url: hexitec_url + 'fp/config/reorder/raw_data',  // Target FP Plugin directly
        contentType: "application/json",
        data: JSON.stringify(raw_data_enable),
        success: function(result) {
            console.log("Raw_data in FP: successfully changed");
        },
        error: function(request, msg, error) {
            console.log("Raw_data in FP: couldn't be changed");
        }
    });

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/reorder/raw_data',  // Target DAQ adapter
        contentType: "application/json",
        data: JSON.stringify(raw_data_enable),
        success: function(result) {
            console.log("Raw_data in daq: successfully changed");
        },
        error: function(request, msg, error) {
            console.log("Raw_data in daq: couldn't be changed");
        }
    });
};

// // curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/detector/fem/dark_correction -d "1"
// var changeDarkCorrectionEnable = function ()
// {
//     dark_correction_enable = $("[name='dark_correction_enable']").bootstrapSwitch('state');
//     $.ajax({
//         type: "PUT",
//         url: hexitec_url + 'detector/fem/dark_correction',
//         contentType: "application/json",
//         data: JSON.stringify(dark_correction_enable),
//         success: function(result) {
//             console.log("dark_correction successfully changed");
//         },
//         error: function(request, msg, error) {
//             console.log("dark_correction couldn't be changed");
//         }
//     });
// };

var changeNextFrameEnable = function ()
{
    next_frame_enable = $("[name='next_frame_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/next_frame/enable',
        contentType: "application/json",
        data: JSON.stringify(next_frame_enable),
        success: function(result) {
            console.log("dark_correction successfully changed");
        },
        error: function(request, msg, error) {
            console.log("dark_correction couldn't be changed");
        }
    });
};

var changeCalibrationEnable = function()
{
    calibration_enable = $("[name='calibration_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/calibration/enable',
        contentType: "application/json",
        data: JSON.stringify(calibration_enable),
        success: function(result) {
            console.log("dark_correction successfully changed");
        },
        error: function(request, msg, error) {
            console.log("dark_correction couldn't be changed");
        }
    });
};

var changeHdfWriteEnable = function()
{
    hdf_write_enable = $("[name='hdf_write_enable']").bootstrapSwitch('state');
    setHdfWrite(hdf_write_enable);
};

//curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/detector -d '{"sensors_layout": "5x5"}' | python -m json.tool
var selectChange = function(sensors_layout)
{
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq',
        contentType: "application/json",
        data: JSON.stringify({"sensors_layout": sensors_layout}),
        success: function(result) {
            $('#sensors-layout-warning').html("");
        },
        error: function(request, msg, error) {
            $('#sensors-layout-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

//curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/detector -d '{"vcal": 1}' | python -m json.tool
var vcalChange = function(vcal)
{
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
        contentType: "application/json",
        data: JSON.stringify({"vcal": parseInt(vcal)}),
        success: function(result) {
            $('#vcal-warning').html("");
        },
        error: function(request, msg, error) {
            $('#vcal-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
}

// setHdfWrite: Helper function to toggle hdf writing on/off
function setHdfWrite(enable)
{
    console.log(" CHANGED setHdfWrite TO TARGET DAQ INSTEAD");
    hdf_write_enable = enable;
    $.ajax({
        type: "PUT",
        // url: hexitec_url + 'fp/config/hdf/write',
        url: hexitec_url + 'detector/daq/file_info/enabled',
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
            }
            else
            {
                console.log("writing is false");
                $('#fr-config').prop('disabled', false);
                $('#fp-config-text').prop('disabled', false);
                $('#hdf-file-path-text').prop('disabled', false);
                $('#hdf-file-name-text').prop('disabled', false);
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
        url: hexitec_url + 'fp/config/config_file',
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

//    curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fr/config/config_file -d "~/develop/projects/odin-demo/hexitec-detector/data/config/fr_hexitec_config.json"
function fr_config_changed()
{
    var fr_config_file = $('#fr-config-text').prop('value');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'fr/config/config_file',
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
//curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/detector/daq/file_info/ -d '{"file_dir": "me_path"}'
function hdf_file_path_changed()
{
    var hdf_file_path = $('#hdf-file-path-text').prop('value');
    var payload = {"file_dir": hdf_file_path};
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/file_info',
        contentType: "application/json",
        data: JSON.stringify(payload),
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

//curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fp/config/hdf/file/name -d "test"
//curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/detector/daq/file_info/ -d '{"file_name": "relts.h5"}'
function hdf_file_name_changed()
{
    var hdf_file_name = $('#hdf-file-name-text').prop('value');
    var payload = {"file_name": hdf_file_name + "_" + showTime()};
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/file_info/',
        contentType: "application/json",
        data: JSON.stringify(payload),
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

// curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/detector/acquisition -d '{"num_frames": 3}'
function frames_changed()
{
    var frames = $('#frames-text').prop('value');
    console.log("frames: " + frames);
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/acquisition/num_frames',
        contentType: "application/json",
        data: (frames),
        success: function(result) {
            $('#frames-warning').html("");
        },
        error: function(request, msg, error) {
            $('#frames-warning').html(error + ": " + format_error_message(request.responseText));
        }
    });
};

function showTime() {
    var timeNow = new Date();
    var hours   = timeNow.getHours();
    var minutes = timeNow.getMinutes();
    var seconds = timeNow.getSeconds();
    var timeString = "" + hours;
    timeString  += ((minutes < 10) ? "0" : "") + minutes;
    timeString  += ((seconds < 10) ? "0" : "") + seconds;
    return timeString;
}
