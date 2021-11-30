api_version = '0.1';
var hexitec_url = '/api/' + api_version + '/hexitec/';

// Vars added for Odin-Data
var raw_data_enable = false;
var processed_data_enable = false;
var addition_enable = false;
var discrimination_enable = false;
var charged_sharing_enable = false;
var next_frame_enable = false;
var calibration_enable = false;
var hdf_write_enable = false;

var duration_enable = false;

var polling_thread_running = false;
var system_health = true;
var fem_error_id = -1;
var ui_frames = 10;
var cold_initialisation = true;

// Called once, when page 1st loaded
$( document ).ready(function()
{
    'use strict';

    $('#odin-control-message').html("Disconnected, Idle");
    $('#odin-control-error').html("No errors");

    // Begin with all except connectButton disabled
    document.getElementById("initialiseButton").disabled = true;
    document.getElementById("acquireButton").disabled = true;
    document.getElementById("cancelButton").disabled = true;
    document.getElementById("disconnectButton").disabled = true;
    document.getElementById("offsetsButton").disabled = true;
    // document.getElementById("hvOnButton").disable = true;
    // document.getElementById("hvOffButton").disable = true;

    /// Style checkboxes into ON/OFF sliders

    $("[name='duration_enable']").bootstrapSwitch();
    $("[name='duration_enable']").bootstrapSwitch('state', duration_enable, true);
    $('input[name="duration_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeDurationEnable();
    });

    $("[name='processed_data_enable']").bootstrapSwitch();
    $("[name='processed_data_enable']").bootstrapSwitch('state', processed_data_enable, true);
    $('input[name="processed_data_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeProcessedDataEnable();
    });

    $("[name='raw_data_enable']").bootstrapSwitch();
    $("[name='raw_data_enable']").bootstrapSwitch('state', raw_data_enable, true);
    $('input[name="raw_data_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeRawDataEnable();
    });

    $("[name='addition_enable']").bootstrapSwitch();
    $("[name='addition_enable']").bootstrapSwitch('state', addition_enable, true);
    $('input[name="addition_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeAdditionEnable();
    });

    $("[name='discrimination_enable']").bootstrapSwitch();
    $("[name='discrimination_enable']").bootstrapSwitch('state', discrimination_enable, true);
    $('input[name="discrimination_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeDiscriminationEnable();
    });

    $("[name='next_frame_enable']").bootstrapSwitch();
    $("[name='next_frame_enable']").bootstrapSwitch('state', next_frame_enable, true);
    $('input[name="next_frame_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeNextFrameEnable();
    });

    $("[name='calibration_enable']").bootstrapSwitch();
    $("[name='calibration_enable']").bootstrapSwitch('state', calibration_enable, true);
    $('input[name="calibration_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
        changeCalibrationEnable();
    });

    // $("[name='hdf_write_enable']").bootstrapSwitch({disabled:true});
    // $("[name='hdf_write_enable']").bootstrapSwitch('state', hdf_write_enable, true);
    // $('input[name="hdf_write_enable"]').on('switchChange.bootstrapSwitch', function(event,state) {
    //     changeHdfWriteEnable();
    // });

    // Apply UI configuration choices
    $('#applyButton').on('click', function(event) {
        apply_ui_values();
    });

    $('#connectButton').on('click', function(event) {
        // On cold initialisation: configure FP, wait 800 ms before connecting
        //  Any subsequent time: Do not configure FP, connect straightaway
        let time_delay = 0;
        if (cold_initialisation) {
            commit_configuration();
            hexitec_config_changed();
            time_delay = 800;
            cold_initialisation = false;
        }

        setTimeout(function() {
            connect_hardware();
            if (polling_thread_running === false)
            {
                polling_thread_running = true;
                start_polling_thread();
            }
        }, time_delay);
        document.getElementById("disconnectButton").disabled = false;
        document.getElementById("connectButton").disabled = true;
    });

    $('#initialiseButton').on('click', function(event) {
        initialise_hardware();
    });

    $('#acquireButton').on('click', function(event) {
        collect_data();
    });

    $('#cancelButton').on('click', function(event) {
        cancel_data();
    });

    $('#disconnectButton').on('click', function(event) {
        disconnect_hardware();
        // Stop polling thread after a 2 second delay to 
        //  allow any lingering message(s) through
        setTimeout(function() {
            polling_thread_running = false;
        }, 2000);
        document.getElementById("disconnectButton").disabled = true;
        document.getElementById("connectButton").disabled = false;
    });

    // $('#hvOnButton').on('click', function(event) {
    //     switch_hv_off();
    //     document.getElementById('hvOnButton').disabled = true;
    //     document.getElementById('hvOffButton').disabled = false;
    // });
    // $('#hvOffButton').on('click', function(event) {
    //     switch_hv_on();
    //     document.getElementById('hvOffButton').disabled = true;
    //     document.getElementById('hvOnButton').disabled = false;
    // });

    $('#offsetsButton').on('click', function(event) {
        collect_offsets();
    });

});

// Supports selecting Charged Sharing algorithm (none/add/dis Buttons)
function setCS(e)
{
    let target = e.target;

    // Define colours to note which button is selected, and which are unselected
    selected = '#0000FF';
    unselected = '#337ab7';
    target.style.backgroundColor = selected;

    charged_sharing_enable = false;
    discrimination_enable = false;
    addition_enable = false;

    switch (target.value)
    {
        case "None":
            document.getElementById("addButton").style.backgroundColor = unselected;
            document.getElementById("disButton").style.backgroundColor = unselected;
            break;
        case "Add":
            document.getElementById("noneButton").style.backgroundColor = unselected;
            document.getElementById("disButton").style.backgroundColor = unselected;
            addition_enable = true;
            charged_sharing_enable = true;
            break;
        case "Dis":
            document.getElementById("noneButton").style.backgroundColor = unselected;
            document.getElementById("addButton").style.backgroundColor = unselected;
            discrimination_enable = true;
            charged_sharing_enable = true;
            break;
        default:
            console.log("You must have added a fourth button, Neither None/Add/Dis pressed");
            break;
    }

    var pixel_grid_size = $('#pixel-grid-size-text').prop('value');

    var addition_payload = {"addition": 
                        {"enable": addition_enable, 
                        "pixel_grid_size": parseInt(pixel_grid_size)} };

    var discrimination_payload = {"discrimination": 
                        {"enable": discrimination_enable, 
                        "pixel_grid_size": parseInt(pixel_grid_size)} };

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config',
        contentType: "application/json",
        data: JSON.stringify(addition_payload),
        error: function(request, msg, error) {
            console.log("FAILED to update Addition plugin settings: " + error);
        }
    });

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config',
        contentType: "application/json",
        data: JSON.stringify(discrimination_payload),
        error: function(request, msg, error) {
            console.log("FAILED to update Discrimination plugin settings: " + error);
        }
    });
}

function switch_hv_off()
{
    console.log("Switching HV off");
}

function switch_hv_on()
{
    console.log("Switching HV on");
}

function collect_offsets()
{
    // Collects offsets used for dark corrections in subsequent acquisitions
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
        contentType: "application/json",
        data: JSON.stringify({"collect_offsets": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function start_polling_thread()
{
    // Starts the polling thread ferrying informationfrom Odin to the UI
    poll_fem();
}

function toggle_ui_elements(bBool)
{
    document.getElementById("initialiseButton").disabled = bBool;
    document.getElementById("acquireButton").disabled = bBool;
    document.getElementById("cancelButton").disabled = bBool;
    // document.getElementById("hvOnButton").disable = bBool;
    document.getElementById("offsetsButton").disabled = bBool;
    document.getElementById("applyButton").disabled = bBool;
    document.getElementById("hdf-file-path-text").disabled = bBool;
    document.getElementById("hdf-file-name-text").disabled = bBool;
    document.getElementById("hexitec-config-text").disabled = bBool;
}

function poll_fem()
{
    // Polls the fem(s) for  hardware status, environmental data, etc

    $.getJSON(hexitec_url + 'fr/status/', function(response)
    {
        var frames = response["value"][0].frames;
        var decoder = response["value"][0].decoder;
        var buffers = response["value"][0].buffers;

        $('#frames_received').html(frames.received);
        $('#frames_released').html(frames.released);
        $('#frames_dropped').html(frames.dropped);
        $('#frames_timedout').html(frames.timedout);

        $('#fem_packets_lost').html(decoder.fem_packets_lost);
        $('#packets_lost').html(decoder.packets_lost);
        $('#buffers_empty').html(buffers.empty);
        $('#buffers_mapped').html(buffers.mapped);
        
        // console.log("Frames; received: " + frames.received + " released: " + frames.released + 
        //                     " dropped: " + frames.dropped + " timedout: " + frames.timedout + "");
        // console.log("r: " + JSON.stringify( response, null, 4));  // fine (object within object)

        // console.log("r[value]: " + JSON.stringify( response["value"], null, 4));    // fine (object within array)
        // console.log("r[value][0]: " + JSON.stringify( response["value"][0], null, 4));  // fine (object within object)
        // console.log("r[value][0].frames: " + response["value"][0].frames);                  //  [object Object]
    });

    $.getJSON(hexitec_url + 'detector', function(response)
    {
        var fems = response["detector"]["fems"]
        var adapter_status = response["detector"]["status"] // adapter.py's status

        var percentage_complete = fems["fem_0"]["operation_percentage_complete"];
        var hardware_connected = fems["fem_0"]["hardware_connected"];
        var hardware_busy = fems["fem_0"]["hardware_busy"];
        
        var polled_frames = fems["fem_0"]["number_frames"];
        
        // if (polled_frames != ui_frames)
        // {
        //     console.log("polled_frames (" + polled_frames + ") != ui_frames (" + ui_frames + ") UPDATE TIME!");
        //     // $('#frames-text').html(polled_frames);      // DOESN'T work
        //     $('#frames-warning').html(polled_frames);   // DOES work, but different type of field
        //     document.getElementById("frames-text").value = polled_frames;
        //     ui_frames = polled_frames;
        // }
        // console.log("frames-text: " + $('#frames-text').val() );
        // // $('#frames-text').html(status_message);

        var adapter_in_progress = response["detector"]["acquisition"]["in_progress"];
        var daq_in_progress = response["detector"]["daq"]["in_progress"];

        // Enable buttons when connection completed
        if (hardware_connected === true)
        {
            if (hardware_busy === true)
            {
                toggle_ui_elements(true);   // Disable
            }
            else
            {
                toggle_ui_elements(false);  // Enable
            }
            if (daq_in_progress === true)
            {
                // Enable cancelButton but disable changing file[path]
                document.getElementById("cancelButton").disabled = false;
                document.getElementById("hdf-file-path-text").disabled = true;
                document.getElementById("hdf-file-name-text").disabled = true;
            }
            else
            {
                // Disable cancelButton but enable changing file[path]
                document.getElementById("cancelButton").disabled = true;
                document.getElementById("hdf-file-path-text").disabled = false;
                document.getElementById("hdf-file-name-text").disabled = false;
            }
        }
        else
        {
            toggle_ui_elements(true);
            // Unlock configuration related UI elements
            document.getElementById("applyButton").disabled = false;
            document.getElementById("hdf-file-path-text").disabled = false;
            document.getElementById("hdf-file-name-text").disabled = false;
            document.getElementById("hexitec-config-text").disabled = false;        
        }

        // http://localhost:8888/api/0.1/hexitec/detector/fems/fem_0/diagnostics/successful_reads
        // Diagnostics:
        // curl -s http://localhost:8888/api/0.1/hexitec/fr/status/ | python -m json.tool
        // curl -s http://localhost:8888/api/0.1/hexitec/detector/fems/fem_0/ | python -m json.tool

        var fem_diagnostics = fems["fem_0"]["diagnostics"];
        var num_reads = fem_diagnostics["successful_reads"];
        var frame_rate = fems["fem_0"]["frame_rate"];
        console.log(hardware_busy + " " + adapter_in_progress + " " + daq_in_progress + 
                    " <= hw_busy, apd_in_prog, daq_in_prog " + "   %_compl: "
                    + fems["fem_0"]["operation_percentage_complete"] 
                    + " reads: " + num_reads + " msg: " + adapter_status["status_message"]);
                    

        $('#frame_rate').html(frame_rate.toFixed(2));

        var acquire_start = fem_diagnostics["acquire_start_time"];
        var acquire_stop = fem_diagnostics["acquire_stop_time"];
        var acquire_time = fem_diagnostics["acquire_time"];
        $('#acquire_start').html(acquire_start);
        $('#acquire_stop').html(acquire_stop);
        $('#acquire_time').html(acquire_time);

        var daq_diagnostics = response["detector"]["daq"]["diagnostics"];
        var daq_start = daq_diagnostics["daq_start_time"];
        var daq_stop = daq_diagnostics["daq_stop_time"];
        var fem_not_busy = daq_diagnostics["fem_not_busy"];

        $('#daq_start').html(daq_start);
        $('#daq_stop').html(daq_stop);
        $('#fem_not_busy').html(fem_not_busy);

        // Obtain overall adapter(.py's) status

        var status_message = adapter_status["status_message"];
        $('#odin-control-message').html(status_message);

        // Get adapter error (either set or empty)
        var status_error = adapter_status["status_error"];
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
            $('#vsr1_hv').html(fems[fem]["vsr1_sensors"]["hv"].toFixed(3));

            $('#vsr2_humidity').html(fems[fem]["vsr2_sensors"]["humidity"].toFixed(2));
            $('#vsr2_ambient').html(fems[fem]["vsr2_sensors"]["ambient"].toFixed(2));
            $('#vsr2_asic1').html(fems[fem]["vsr2_sensors"]["asic1"].toFixed(2));
            $('#vsr2_asic2').html(fems[fem]["vsr2_sensors"]["asic2"].toFixed(2));
            $('#vsr2_adc').html(fems[fem]["vsr2_sensors"]["adc"].toFixed(2));
            $('#vsr2_hv').html(fems[fem]["vsr2_sensors"]["hv"].toFixed(3));

            $('#vsr1_sync').html(fems[fem]["vsr1_sync"]);
            $('#vsr2_sync').html(fems[fem]["vsr2_sync"]);

            // console.log("fem id: '" + fems[fem]["id"] + "' health: '" + fems[fem]["health"] + "' stat msg: '" + fems[fem]["status_message"] + "'.");
        }

        // system_health    // true=all fem(s) OK, false=fem(s) bad, fem_error_id says which one
        // fem_error_id

        // Traffic "light" green/red to indicate system good/bad

        lampDOM = document.getElementById("Green");

        // Clear status if camera disconnected, otherwise look for any error
        if (status_message === "Camera disconnected")
        {
            lampDOM.classList.remove("lampGreen");
            lampDOM.classList.remove("lampRed");
        }
        else
        {
            if (status_error.length  === 0)
            {
                lampDOM.classList.add("lampGreen");
            }
            else
            {
                lampDOM.classList.remove("lampGreen");
                lampDOM.classList.add("lampRed");
            }
        }

        var progress_element = document.getElementById("progress-odin");
        progress_element.value = percentage_complete;

        if (polling_thread_running === true)
        {
            window.setTimeout(poll_fem, 850);
        }
    });
}

function connect_hardware()
{
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
        contentType: "application/json",
        data: JSON.stringify({"connect_hardware": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function initialise_hardware()
{
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
        contentType: "application/json",
        data: JSON.stringify({"initialise_hardware": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function collect_data()
{
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/acquisition',
        contentType: "application/json",
        data: JSON.stringify({"start_acq": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function cancel_data()
{
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/acquisition',
        contentType: "application/json",
        data: JSON.stringify({"stop_acq": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function disconnect_hardware()
{
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
        contentType: "application/json",
        data: JSON.stringify({"disconnect_hardware": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function commit_configuration()
{
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector',
        contentType: "application/json",
        data: JSON.stringify({"commit_configuration": ""}),
        success: function(result) {
            $('#odin-control-warning').html("");
        },
        error: function(request, msg, error) {
            $('#odin-control-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function send_sequence_file(path, file)
{
    // Sends a configuration sequence file to Odin control
    $.ajax({
        type: "PUT",
        url: path,
        contentType: "application/json",
        data: file,
        error: function(request, msg, error) {
            console.log("Failed to load configuration file: " + file);
        }
    });
}

// apply_ui_values: Disconnect existing sequence of plugins, 
//  load the sequence of plugins corresponding to UI settings
function apply_ui_values()
{
    if (cold_initialisation) {
        cold_initialisation = false;
    }
    // Load all UI settings into HexitecDAQ's ParameterTree

    // Generate temporary config file(s) loading plugins chain,
    //  push HexitecDAQ's ParameterTree settings to FP's plugins
    commit_configuration();

    // Read configuration file into memory, recalculate frame_rate
    hexitec_config_changed();

    // This will be executed after however many milliseconds 
    //  specified at the end of this function definition
    setTimeout(function() {

        // Delay necessary otherwise some plugins' variables are configured 
        // before they are actually loaded (which will not work obviously)

        changeRawDataEnable();
        changeProcessedDataEnable();
        threshold_mode_changed();
        threshold_value_changed();
        var threshold_mode = $('#threshold-mode-text').prop('value');
        // Update threshold filename if threshold filename mode set
        //  (0: strings equal [filename mode], 1: not [none/value mode])
        if (threshold_mode.localeCompare("filename") === 0)
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
        
        // (Re-)set duration/frames as hexitec config may have changed frame_rate
        changeDurationEnable();
    }, 300);
}

function threshold_filename_changed()
{
    // Update threshold filename if threshold filename mode set
    //  (0: strings equal [filename mode], 1: not [none/value mode])
    var threshold_mode = $('#threshold-mode-text').prop('value');
    if (threshold_mode.localeCompare("filename") === 0)
    {
        var threshold_filename = $('#threshold-filename-text').prop('value');
        threshold_filename = JSON.stringify(threshold_filename);
        $.ajax({
            type: "PUT",
            url: hexitec_url + 'detector/daq/config/threshold/threshold_filename',
            contentType: "application/json",
            data: threshold_filename,
            success: function(result) {
                $('#threshold-filename-warning').html("");
            },
            error: function(request, msg, error) {
                $('#threshold-filename-warning').html(error + ": " + format_error(request.responseText));
            }
        });
    }
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
            $('#threshold-value-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function threshold_mode_changed()
{
    var threshold_mode = $('#threshold-mode-text').prop('value');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/threshold/threshold_mode',
        contentType: "application/json",
        data: JSON.stringify(threshold_mode),
        success: function(result) {
            $('#threshold-mode-warning').html("");
            document.getElementById("threshold-mode-warning").classList.remove('alert-danger');
        },
        error: function(request, msg, error) {
            $('#threshold-mode-warning').html(error + ": " + format_error(request.responseText));
            document.getElementById("threshold-mode-warning").classList.add('alert-danger');
        }
    });
    // Check valid filename/Update threshold filename if threshold filename mode set
    //  (0: strings equal [filename mode], 1: not [none/value mode])
    if (threshold_mode.localeCompare("filename") === 0)
    {
        threshold_filename_changed();
    }
}

function gradients_filename_changed()
{
    // Only check/update gradients filename if calibration is enabled
    if (calibration_enable === true)
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
                $('#gradients-filename-warning').html(error + ": " + format_error(request.responseText));
            }
        });
    }
}

function intercepts_filename_changed()
{
    // Only check/update intercepts filename if calibration is enabled
    if (calibration_enable === true)
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
                $('#intercepts-filename-warning').html(error + ": " + format_error(request.responseText));
            }
        });
    }
}

function pixel_grid_size_changed()
{
    // Sends the setting to both Addition, Discrimination plugins

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
            $('#pixel-grid-size-warning').html(error + ": " + format_error(request.responseText));
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
            $('#pixel-grid-size-warning').html(error + ": " + format_error(request.responseText));
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
            $('#bin-start-warning').html(error + ": " + format_error(request.responseText));
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
            $('#bin-end-warning').html(error + ": " + format_error(request.responseText));
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
            $('#bin-width-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

var changeDurationEnable = function()
{
    // Change whether duration/frame selected
    duration_enable = $("[name='duration_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/acquisition/duration_enable',
        contentType: "application/json",
        data: JSON.stringify(duration_enable),
        error: function(request, msg, error) {
            console.log("Duration enable couldn't be changed");
        }
    });

    if (duration_enable)
    {
        $('#duration-text').prop('disabled', false);
        $('#frames-text').prop('disabled', true);
    }
    else
    {
        $('#duration-text').prop('disabled', true);
        $('#frames-text').prop('disabled', false);
        frames_changed();
    }
};

var changeProcessedDataEnable = function()
{
    // TODO: Temporarily hacked until Odin Control supports bool
    processed_data_enable = $("[name='processed_data_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'fp/config/histogram/pass_processed',  // Targets FP Plugin directly
        contentType: "application/json",
        data: JSON.stringify(processed_data_enable),
        error: function(request, msg, error) {
            console.log("Processed dataset in FP: couldn't be changed");
        }
    });

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/histogram/pass_processed',  // Targets DAQ adapter
        contentType: "application/json",
        data: JSON.stringify(processed_data_enable),
        error: function(request, msg, error) {
            console.log("Processed dataset in daq: couldn't be changed");
        }
    });
};

var changeRawDataEnable = function()
{
    // TODO: Temporarily hacked until Odin control supports bool
    raw_data_enable = $("[name='raw_data_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'fp/config/histogram/pass_raw',  // Targets FP Plugin directly
        contentType: "application/json",
        data: JSON.stringify(raw_data_enable),
        error: function(request, msg, error) {
            console.log("Raw_data in FP: couldn't be changed");
        }
    });

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/histogram/pass_raw',  // Targets DAQ adapter
        contentType: "application/json",
        data: JSON.stringify(raw_data_enable),
        error: function(request, msg, error) {
            console.log("Raw_data in daq: couldn't be changed");
        }
    });
};

var changeNextFrameEnable = function()
{
    next_frame_enable = $("[name='next_frame_enable']").bootstrapSwitch('state');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/next_frame/enable',
        contentType: "application/json",
        data: JSON.stringify(next_frame_enable),
        error: function(request, msg, error) {
            console.log("Next frame couldn't be changed");
        }
    });
};

var changeCalibrationEnable = function()
{
    calibration_enable = $("[name='calibration_enable']").bootstrapSwitch('state');

    if (calibration_enable)
    {
        $('#bin_start').html("Bin Start: [keV]&nbsp;");
        $('#bin_end').html("Bin End: [keV]&nbsp;");
        $('#bin_width').html("Bin Width: [keV]&nbsp;");
        document.getElementById("bin-start-text").value = 0;
        document.getElementById("bin-end-text").value = 200;
        document.getElementById("bin-width-text").value = 0.25;
    }
    else
    {
        $('#bin_start').html("Bin Start: [ADU]&nbsp;");
        $('#bin_end').html("Bin End: [ADU]&nbsp;");
        $('#bin_width').html("Bin Width: [ADU]&nbsp;");
        document.getElementById("bin-start-text").value = 0;
        document.getElementById("bin-end-text").value = 8000;
        document.getElementById("bin-width-text").value = 10;
   }

    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/config/calibration/enable',
        contentType: "application/json",
        data: JSON.stringify(calibration_enable),
        error: function(request, msg, error) {
            console.log("calibration enable couldn't be changed");
        }
    });

    // If calibration now enabled, check coefficient files are valid
    if (calibration_enable)
    {
        gradients_filename_changed();
        intercepts_filename_changed()
    }
};

var changeHdfWriteEnable = function()
{
    hdf_write_enable = $("[name='hdf_write_enable']").bootstrapSwitch('state');
    setHdfWrite(hdf_write_enable);
};

var sensorsLayoutChange = function(sensors_layout)
{
    // Sets hardware sensors Configuration; i.e. number of rows and columns of sensors
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq',
        contentType: "application/json",
        data: JSON.stringify({"sensors_layout": sensors_layout}),
        success: function(result) {
            $('#sensors-layout-warning').html("");
        },
        error: function(request, msg, error) {
            $('#sensors-layout-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

var compressionChange = function(compression)
{
    // Sets compression on (blosc) or off (none)
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq',
        contentType: "application/json",
        data: JSON.stringify({"compression_type": compression}),
        success: function(result) {
            $('#compression-warning').html("");
        },
        error: function(request, msg, error) {
            $('#compression-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function setHdfWrite(enable)
{
    // Helper function to toggle hdf writing on/off

    hdf_write_enable = enable;
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/daq/file_info/enabled',
        contentType: "application/json",
        data: JSON.stringify(hdf_write_enable),
        success: function(result) {
            $('#hdf-write-enable-warning').html("");
            // If write enabled, must disable access to config files, 
            //  file path & name and frames (vice versa if disabled)
            if (hdf_write_enable === true)
            {
                $('#hdf-file-path-text').prop('disabled', true);
                $('#hdf-file-name-text').prop('disabled', true);
            }
            else
            {
                $('#hdf-file-path-text').prop('disabled', false);
                $('#hdf-file-name-text').prop('disabled', false);
            }
        },
        error: function(request, msg, error) {
            $('#hdf-write-enable-warning').html(error + ": " + format_error(request.responseText));
        }
    });
}

function format_error(error)
{
    // Format error messages before they are displayed in the UI
    // Error messages typically look like: 
    //  "error": "File name must not be empty"
    //  strip out '"error":' bit so it becomes: '"File name must not be empty"'
    var withoutQuotation = error.replace(/"/g,'');
    var withoutBrackets = withoutQuotation.replace('{', '').replace('}', '');
    return withoutBrackets.replace('error: ','');
}

function fp_config_changed()
{
    // Change fp configuration file
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
            $('#fp-config-warning').html(error + ": " + format_error(request.responseText));
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

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
            $('#fr-config-warning').html(error + ": " + format_error(request.responseText));
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

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
            $('#hdf-file-path-warning').html(error + ": " + format_error(request.responseText));
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

function hdf_file_name_changed()
{
    // Appends timestamp to filename, updates hdf file name

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
            $('#hdf-file-name-warning').html(error + ": " + format_error(request.responseText));
            $("[name='hdf_write_enable']").bootstrapSwitch('disabled', true);
        }
    });
};

function hexitec_config_changed()
{
    var hexitec_config = $('#hexitec-config-text').prop('value');
    var payload = {"hexitec_config": hexitec_config};
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/fems/fem_0/',
        contentType: "application/json",
        data: JSON.stringify(payload),
        success: function(result) {
            $('#hexitec-config-warning').html("");
        },
        error: function(request, msg, error) {
            $('#hexitec-config-warning').html(error + ": " + format_error(request.responseText));
        }
    });
};

function frames_changed()
{
    var ui_frames = $('#frames-text').prop('value');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/acquisition/number_frames',
        contentType: "application/json",
        data: (ui_frames),
        success: function(result) {
            $('#frames-warning').html("");
        },
        error: function(request, msg, error) {
            $('#frames-warning').html(error + ": " + format_error(request.responseText));
        }
    });
};

function duration_changed()
{
    var duration = $('#duration-text').prop('value');
    $.ajax({
        type: "PUT",
        url: hexitec_url + 'detector/acquisition/duration',
        contentType: "application/json",
        data: (duration),
        success: function(result) {
            $('#duration-warning').html("");
        },
        error: function(request, msg, error) {
            $('#duration-warning').html(error + ": " + format_error(request.responseText));
        }
    });
};

function showTime()
{
    // Returns a timestamp string in the format "YYYYMMDD_HHMMSS"
    var timeNow = new Date();
    var years   = timeNow.getUTCFullYear();
    var months  = timeNow.getUTCMonth() + 1; // Make January=1, February=2, etc
    var days    = timeNow.getUTCDate();
    var hours   = timeNow.getHours();
    var minutes = timeNow.getMinutes();
    var seconds = timeNow.getSeconds();
    // Date uses minimal number of digits; January 1 or 01/01 is
    //  represented by 1/1. Force use 2 digits representation:
    days = ((days < 10) ? "0" : "") + days;
    hours = ((hours <10) ? "0" : "") + hours;
    months = ((months < 10) ? "0" : "") + months;
    minutes = ((minutes < 10) ? "0" : "") + minutes;
    seconds = ((seconds < 10) ? "0" : "") + seconds;

    var timeString  = "" + years;
    timeString += months;
    timeString += days;
    timeString += "_" + hours;
    timeString += minutes;
    timeString += seconds;
    return timeString;
}
