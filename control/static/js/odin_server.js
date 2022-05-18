api_version = '0.1';
const hexitec_url = '/api/' + api_version + '/hexitec/';

let hexitec_endpoint;

// Vars added for Odin-Data
var raw_data_enable = false;
var processed_data_enable = false;
var addition_enable = false;
var discrimination_enable = false;
var charged_sharing_enable = false;
var next_frame_enable = false;
var calibration_enable = false;

var duration_enable = false;

var polling_thread_running = false;
var system_health = true;
var fem_error_id = -1;
var ui_frames = 10;
var cold_initialisation = true;
var hv_enabled = false;

// Called once, when page 1st loaded
document.addEventListener("DOMContentLoaded", function()
{
    hexitec_endpoint = new AdapterEndpoint("hexitec");
    'use strict';

    document.querySelector('#odin-control-message').innerHTML = "Disconnected, Idle";
    document.querySelector('#odin-control-error').innerHTML = "No errors";

    // Begin with all except connectButton disabled
    document.querySelector('#initialiseButton').disabled = true;
    document.querySelector('#acquireButton').disabled = true;
    document.querySelector('#cancelButton').disabled = true;
    document.querySelector('#disconnectButton').disabled = true;
    document.querySelector('#offsetsButton').disabled = true;
    document.querySelector('#hvOnButton').disabled = true;
    document.querySelector('#hvOffButton').disabled = true;
});

// Apply UI configuration choices
function applyButtonClicked()
{
    console.log("appliedButton");
    apply_ui_values();
}

function applyButton2Clicked()
{
    console.log("applyButton 2");
    apply_ui_values();
}

function connectButtonClicked()
{
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
    document.querySelector('#disconnectButton').disabled = false;
    document.querySelector('#connectButton').disabled = true;
}

function hvOnButtonClicked()
{
    // TODO: Switch HV on
    hv_enabled = true;
    document.querySelector('#hvOnButton').disabled = true;
    document.querySelector('#hvOffButton').disabled = false;
    console.log("Switching HV on");
}

function hvOffButtonClicked()
{
    // TODO: Switch HV off
    hv_enabled = false;
    document.querySelector('#hvOnButton').disabled = false;
    document.querySelector('#hvOffButton').disabled = true;
    console.log("Switching HV off");
}

function initialiseButtonClicked()
{
    initialise_hardware();
}

function offsetsButtonClicked()
{
    collect_offsets();
}

function acquireButtonClicked()
{
    collect_data();
}

function cancelButtonClicked()
{
    cancel_data();
}

function disconnectButtonClicked()
{
    disconnect_hardware();
    // Stop polling thread after a 2 second delay to 
    //  allow any lingering message(s) through
    setTimeout(function() {
        polling_thread_running = false;
    }, 2000);
    document.querySelector('#disconnectButton').disabled = true;
    document.querySelector('#connectButton').disabled = false;
}

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

    var pixel_grid_size = document.querySelector('#pixel-grid-size-text').value;

    var addition_payload = {"addition": 
                        {"enable": addition_enable, 
                        "pixel_grid_size": parseInt(pixel_grid_size)} };

    var discrimination_payload = {"discrimination": 
                        {"enable": discrimination_enable, 
                        "pixel_grid_size": parseInt(pixel_grid_size)} };

    hexitec_endpoint.put(addition_payload, 'detector/daq/config')
    .then(result => {
        // console.log("Updating Addition successful");
    })
    .catch(error => {
        console.log("FAILED to update Addition: " + error.message);
    });

    hexitec_endpoint.put(discrimination_payload, 'detector/daq/config')
    .then(result => {
        // console.log("Updating Discrimination successful");
    })
    .catch(error => {
        console.log("FAILED to update Discrimination: " + error.message);
    });
}

function start_polling_thread()
{
    // Starts the polling thread ferrying information from Odin to the UI
    poll_fem();
}

function toggle_ui_elements(bBool)
{
    document.querySelector('#initialiseButton').disabled = bBool;
    document.querySelector('#acquireButton').disabled = bBool;
    document.querySelector('#cancelButton').disabled = bBool;
    if (hv_enabled)
        document.querySelector('#hvOffButton').disabled = bBool;
    else
        document.querySelector('#hvOnButton').disabled = bBool;
    document.querySelector('#offsetsButton').disabled = bBool;
    document.querySelector('#applyButton').disabled = bBool;
    document.querySelector('#applyButton2').disabled = bBool;
    document.querySelector('#hdf-file-path-text').disabled = bBool;
    document.querySelector('#hdf-file-name-text').disabled = bBool;
    document.querySelector('#hexitec-config-text').disabled = bBool;
}

function poll_fem()
{
    // Polls the fem(s) for hardware status, environmental data, etc
    hexitec_endpoint.get_url(hexitec_url + 'fr/status/')
    .then(result => {
        const frames = result["value"][0].frames;
        const decoder = result["value"][0].decoder;
        const buffers = result["value"][0].buffers;

        document.querySelector('#frames_received').innerHTML = frames.received;
        document.querySelector('#frames_released').innerHTML = frames.released;
        document.querySelector('#frames_dropped').innerHTML = frames.dropped;
        document.querySelector('#frames_timedout').innerHTML = frames.timedout;

        document.querySelector('#fem_packets_lost').innerHTML = decoder.fem_packets_lost;
        document.querySelector('#packets_lost').innerHTML = decoder.packets_lost;
        document.querySelector('#buffers_empty').innerHTML = buffers.empty;
        document.querySelector('#buffers_mapped').innerHTML = buffers.mapped;
    })
    .catch(error => {
        console.log("poll_fem(), fr: " + error.message);
    });

    hexitec_endpoint.get_url(hexitec_url + 'detector')
    .then(result => {
        const fem = result["detector"]["fem"]
        const adapter_status = result["detector"]["status"] // adapter.py's status

        const percentage_complete = fem["operation_percentage_complete"];
        const hardware_connected = fem["hardware_connected"];
        const hardware_busy = fem["hardware_busy"];
        
        const adapter_in_progress = result["detector"]["acquisition"]["in_progress"];   // Debug info
        const daq_in_progress = result["detector"]["daq"]["in_progress"];

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
                document.querySelector('#cancelButton').disabled = false;
                document.querySelector('#hdf-file-path-text').disabled = true;
                document.querySelector('#hdf-file-name-text').disabled = true;
            }
            else
            {
                // Disable cancelButton but enable changing file[path]
                document.querySelector('#cancelButton').disabled = true;
                document.querySelector('#hdf-file-path-text').disabled = false;
                document.querySelector('#hdf-file-name-text').disabled = false;
            }
        }
        else
        {
            toggle_ui_elements(true);
            // Unlock configuration related UI elements
            document.querySelector('#applyButton').disabled = false;
            document.querySelector('#applyButton2').disabled = false;
            document.querySelector('#hdf-file-path-text').disabled = false;
            document.querySelector('#hdf-file-name-text').disabled = false;
            document.querySelector('#hexitec-config-text').disabled = false;        
        }

        var fem_diagnostics = fem["diagnostics"];
        var num_reads = fem_diagnostics["successful_reads"];
        var frame_rate = fem["frame_rate"];
        document.querySelector('#frame_rate').innerHTML = frame_rate.toFixed(2);

        /// UNCOMMENT ME
        // console.log(hardware_busy + " " + adapter_in_progress + " " + daq_in_progress + 
        //             " <= hw_busy, apd_in_prog, daq_in_prog " + "   %_compl: "
        //             + fem["operation_percentage_complete"] 
        //             + " reads: " + num_reads + " msg: " + adapter_status["status_message"]);

        var acquire_start = fem_diagnostics["acquire_start_time"];
        var acquire_stop = fem_diagnostics["acquire_stop_time"];
        var acquire_time = fem_diagnostics["acquire_time"];
        document.querySelector('#acquire_start').innerHTML = acquire_start;
        document.querySelector('#acquire_stop').innerHTML = acquire_stop;
        document.querySelector('#acquire_time').innerHTML = acquire_time;

        var daq_diagnostics = result["detector"]["daq"]["diagnostics"];
        var daq_start = daq_diagnostics["daq_start_time"];
        var daq_stop = daq_diagnostics["daq_stop_time"];
        var fem_not_busy = daq_diagnostics["fem_not_busy"];
        document.querySelector('#daq_start').innerHTML = daq_start;
        document.querySelector('#daq_stop').innerHTML = daq_stop;
        document.querySelector('#fem_not_busy').innerHTML = fem_not_busy;

        // Obtain overall adapter(.py's) status

        var status_message = adapter_status["status_message"];
        document.querySelector('#odin-control-message').innerHTML = status_message;

        // Get adapter error (either set or empty)
        const status_error = adapter_status["status_error"];
        var status = "";
        if (status_error.length > 0)
        {
            status = "Error: '" + status_error + "'";
        }
        document.querySelector('#odin-control-error').innerHTML = status;

        document.querySelector('#vsr1_humidity').innerHTML = fem["vsr1_sensors"]["humidity"].toFixed(2);
        document.querySelector('#vsr1_ambient').innerHTML = fem["vsr1_sensors"]["ambient"].toFixed(2);
        document.querySelector('#vsr1_asic1').innerHTML = fem["vsr1_sensors"]["asic1"].toFixed(2);
        document.querySelector('#vsr1_asic2').innerHTML = fem["vsr1_sensors"]["asic2"].toFixed(2);
        document.querySelector('#vsr1_adc').innerHTML = fem["vsr1_sensors"]["adc"].toFixed(2);
        document.querySelector('#vsr1_hv').innerHTML = fem["vsr1_sensors"]["hv"].toFixed(3);
        document.querySelector('#vsr1_sync').innerHTML = fem["vsr1_sync"];

        document.querySelector('#vsr2_humidity').innerHTML = fem["vsr2_sensors"]["humidity"].toFixed(2);
        document.querySelector('#vsr2_ambient').innerHTML = fem["vsr2_sensors"]["ambient"].toFixed(2);
        document.querySelector('#vsr2_asic1').innerHTML = fem["vsr2_sensors"]["asic1"].toFixed(2);
        document.querySelector('#vsr2_asic2').innerHTML = fem["vsr2_sensors"]["asic2"].toFixed(2);
        document.querySelector('#vsr2_adc').innerHTML = fem["vsr2_sensors"]["adc"].toFixed(2);
        document.querySelector('#vsr2_hv').innerHTML = fem["vsr2_sensors"]["hv"].toFixed(3);
        document.querySelector('#vsr2_sync').innerHTML = fem["vsr2_sync"];

        /// To be implemented: system_health - true=fem OK, false=fem bad

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
    })
    .catch(error => {
        console.log("poll_fem(), detector: " + error.message);
    });
}

function connect_hardware()
{
    hexitec_endpoint.put({"connect_hardware": ""}, 'detector')
    .then(result => {
        document.querySelector('#odin-control-error').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#odin-control-error').innerHTML = error.message;
    });
}

function initialise_hardware()
{
    hexitec_endpoint.put({"initialise_hardware": ""}, 'detector')
    .then(result => {
        document.querySelector('#odin-control-error').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#odin-control-error').innerHTML = error.message;
    });
}

function collect_offsets()
{
    // Collects offsets used for dark corrections in subsequent acquisitions
    hexitec_endpoint.put({"collect_offsets": ""}, 'detector')
    .then(result => {
        document.querySelector('#odin-control-error').innerHTML =  "";
    })
    .catch(error => {
        document.querySelector('#odin-control-error').innerHTML = error.message;
    });
}

function collect_data()
{
    hexitec_endpoint.put({"start_acq": ""}, 'detector/acquisition')
    .then(result => {
        document.querySelector('#odin-control-error').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#odin-control-error').innerHTML = error.message;
    });
}

function cancel_data()
{
    hexitec_endpoint.put({"stop_acq": ""}, 'detector/acquisition')
    .then(result => {
        document.querySelector('#odin-control-error').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#odin-control-error').innerHTML = error.message;
    });
}

function disconnect_hardware()
{
    hexitec_endpoint.put({"disconnect_hardware": ""}, 'detector')
    .then(result => {
        document.querySelector('#odin-control-error').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#odin-control-error').innerHTML = error.message;
    });
}

function commit_configuration()
{
    hexitec_endpoint.put({"commit_configuration": ""}, 'detector')
    .then(result => {
        document.querySelector('#odin-control-error').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#odin-control-error').innerHTML = error.message;
    });
}

// apply_ui_values: Disconnect existing sequence of plugins, 
//  load the sequence of plugins corresponding to UI settings
function apply_ui_values()
{
    if (cold_initialisation) {
        // console.log("apply_UI_values() - cold_initialisation");
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
        var threshold_mode = document.querySelector('#threshold-mode-text').value;
        // console.log("apply_UI_values)), comparison: " + threshold_mode.localeCompare("filename"));
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
        changeModeEnable();
    }, 300);
}

function threshold_filename_changed()
{
    // Update threshold filename if threshold filename mode set
    //  (0: strings equal [filename mode], 1: not [none/value mode])
    var threshold_mode = document.querySelector('#threshold-mode-text').value;
    // console.log("threshold_filename_changed, comparison: " + threshold_mode.localeCompare("filename"));
    if (threshold_mode.localeCompare("filename") === 0)
    {
        var threshold_filename = document.querySelector('#threshold-filename-text').value;
        hexitec_endpoint.put(threshold_filename, 'detector/daq/config/threshold/threshold_filename')
        .then(result => {
            document.querySelector('#threshold-filename-warning').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#threshold-filename-warning').innerHTML = error.message;
        });
    }
}

function threshold_value_changed()
{
    var threshold_value = document.querySelector('#threshold-value-text').value;
    hexitec_endpoint.put(parseInt(threshold_value), 'detector/daq/config/threshold/threshold_value')
    .then(result => {
        document.querySelector('#threshold-value-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#threshold-value-warning').innerHTML = error.message;
    });
}

function threshold_mode_changed()
{
    var threshold_mode = document.querySelector('#threshold-mode-text').value;
    hexitec_endpoint.put(threshold_mode, 'detector/daq/config/threshold/threshold_mode')
    .then(result => {
        document.querySelector('#threshold-mode-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#threshold-mode-warning').innerHTML = error.message;
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
        var gradients_filename = document.querySelector('#gradients-filename-text').value;
        hexitec_endpoint.put(gradients_filename, 'detector/daq/config/calibration/gradients_filename')
        .then(result => {
            document.querySelector('#gradients-filename-warning').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#gradients-filename-warning').innerHTML = error.message;
        });
    }
}

function intercepts_filename_changed()
{
    // Only check/update intercepts filename if calibration is enabled
    if (calibration_enable === true)
    {
        var intercepts_filename = document.querySelector('#intercepts-filename-text').value;
        hexitec_endpoint.put(intercepts_filename, 'detector/daq/config/calibration/intercepts_filename')
        .then(result => {
            document.querySelector('#intercepts-filename-warning').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#intercepts-filename-warning').innerHTML = error.message;
        });
    }
}

function pixel_grid_size_changed()
{
    var pixel_grid_size = document.querySelector('#pixel-grid-size-text').value;

    hexitec_endpoint.put(parseInt(pixel_grid_size), 'detector/daq/config/addition/pixel_grid_size')
    .then(result => {
        document.querySelector('#pixel-grid-size-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#pixel-grid-size-warning').innerHTML = error.message;
    });

    hexitec_endpoint.put(parseInt(pixel_grid_size), 'detector/daq/config/discrimination/pixel_grid_size')
    .then(result => {
        document.querySelector('#pixel-grid-size-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#pixel-grid-size-warning').innerHTML = error.message;
    });
}

function bin_start_changed()
{
    var bin_start = document.querySelector('#bin-start-text').value;
    hexitec_endpoint.put(parseInt(bin_start), 'detector/daq/config/histogram/bin_start')
    .then(result => {
        document.querySelector('#bin-start-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#bin-start-warning').innerHTML = error.message;
    });
}

function bin_end_changed()
{
    var bin_end = document.querySelector('#bin-end-text').value;
    hexitec_endpoint.put(parseInt(bin_end), 'detector/daq/config/histogram/bin_end')
    .then(result => {
        document.querySelector('#bin-end-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#bin-end-warning').innerHTML = error.message;
    });
}

function bin_width_changed()
{
    var bin_width = document.querySelector('#bin-width-text').value;
    hexitec_endpoint.put(parseFloat(bin_width), 'detector/daq/config/histogram/bin_width')
    .then(result => {
        document.querySelector('#bin-width-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#bin-width-warning').innerHTML = error.message;
    });
}

// Change (Duration) mode, true if Seconds selected, false = Frames selected
function changeModeEnable()
{
    duration_enable = document.getElementById('mode_radio1').checked;

    hexitec_endpoint.put(duration_enable, 'detector/acquisition/duration_enable')
    .then(result => {
        // console.log("duration enable  updated");
    })
    .catch(error => {
        console.log("duration enable: couldn't be changed: " + error.message);
    });

    if (duration_enable)
    {
        document.querySelector('#duration-text').disabled = false;
        document.querySelector('#frames-text').disabled = true;
        duration_changed();
    }
    else
    {
        document.querySelector('#duration-text').disabled = true;
        document.querySelector('#frames-text').disabled = false;
        frames_changed();
    }
};

function changeProcessedDataEnable()
{
    // Odin Control do not support bool, must target FP and DAQ adapter
    processed_data_enable = document.getElementById('processed_data_radio1').checked;

    processed_data_enable = JSON.stringify(processed_data_enable);
    processed_data_enable = (processed_data_enable === "true");
    hexitec_endpoint.put(processed_data_enable, 'fp/config/histogram/pass_processed')
    .then(result => {
        // console.log("changeProcessDataEnabled fp updated");
    })
    .catch(error => {
        console.log("Processed dataset in FP: couldn't be changed: " + errorr.message);
    });

    hexitec_endpoint.put(processed_data_enable, 'detector/daq/config/histogram/pass_processed')
    .then(result => {
        // console.log("changeProcessDataEnabled daq updated");
    })
    .catch(error => {
        console.log("Processed dataset in daq: couldn't be changed: " + error.message);
    });
};

function changeRawDataEnable()
{
    // Odin Control do not support bool, must target FP and DAQ adapter
    raw_data_enable = document.getElementById('raw_data_radio1').checked;
    
    raw_data_enable = JSON.stringify(raw_data_enable);
    raw_data_enable = (raw_data_enable === "true");
    hexitec_endpoint.put(raw_data_enable, 'fp/config/histogram/pass_raw')
    .then(result => {
        // console.log("changeRawDataEnable fp updated");
    })
    .catch(error => {
        console.log("Raw dataset in FP: couldn't be changed: " + error.message);
    });

    hexitec_endpoint.put(raw_data_enable, 'detector/daq/config/histogram/pass_raw')
    .then(result => {
        // console.log("changeRawDataEnable daq updated");
    })
    .catch(error => {
        console.log("Raw dataset in daq: couldn't be changed: " + error.message);
    });
};

function changeNextFrameEnable()
{
    next_frame_enable = document.getElementById('next_frame_radio1').checked;
    next_frame_enable = JSON.stringify(next_frame_enable);
    next_frame_enable = (next_frame_enable === "true");
    hexitec_endpoint.put(next_frame_enable, 'detector/daq/config/next_frame/enable')
    .then(result => {
        // console.log("changeFrameEnable OK");
    })
    .catch(error => {
        console.log("Next Frame couldn't be changed: " + error.message);
    });
};

function changeCalibrationEnable()
{
    calibration_enable = document.getElementById('calibration_radio1').checked;
    calibration_enable = JSON.stringify(calibration_enable);
    calibration_enable = (calibration_enable === "true");

    if (calibration_enable)
    {
        document.querySelector('#bin_start').innerHTML = "Bin Start: [keV]&nbsp;";
        document.querySelector('#bin_end').innerHTML = "Bin End: [keV]&nbsp;";
        document.querySelector('#bin_width').innerHTML = "Bin Width: [keV]&nbsp;";
        document.querySelector('#bin-start-text').value = 0;
        document.querySelector('#bin-end-text').value = 200;
        document.querySelector('#bin-width-text').value = 0.25;
    }
    else
    {
        document.querySelector('#bin_start').innerHTML = "Bin Start: [ADU]&nbsp;";
        document.querySelector('#bin_end').innerHTML = "Bin End: [ADU]&nbsp;";
        document.querySelector('#bin_width').innerHTML = "Bin Width: [ADU]&nbsp;";
        document.querySelector('#bin-start-text').value = 0;
        document.querySelector('#bin-end-text').value = 8000;
        document.querySelector('#bin-width-text').value = 10;
   }

    hexitec_endpoint.put(calibration_enable, 'detector/daq/config/calibration/enable')
    .then(result => {
        // console.log(" calibration_enable success");
    })
    .catch(error => {
        console.log("calibration_enable failed: " + error.message);
    });

    // If calibration now enabled, check coefficients files are valid
    if (calibration_enable)
    {
        gradients_filename_changed();
        intercepts_filename_changed()
    }
};

function sensorsLayoutChange(sensors_layout)
{
    // Sets hardware sensors Configuration; i.e. number of rows and columns of sensors
    hexitec_endpoint.put({"sensors_layout": sensors_layout}, 'detector/daq')
    .then(result => {
        document.querySelector('#sensors-layout-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#sensors-layout-warning').innerHTML = error.message;
    });
}

function numberNodesChange(number_nodes)
{
    // Sets number of FR/FP (pair of) nodes
    hexitec_endpoint.put(parseInt(number_nodes), 'detector/status/number_nodes')
    .then(result => {
        document.querySelector('#number-nodes-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#number-nodes-warning').innerHTML = error.message;
    });
}

function compressionChange(compression)
{
    // Sets compression on (blosc) or off (none)
    hexitec_endpoint.put({"compression_type": compression}, 'detector/daq')
    .then(result => {
        document.querySelector('#compression-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#compression-warning').innerHTML = error.message;
    });
}

function hdf_file_path_changed()
{
    var hdf_file_path = document.querySelector('#hdf-file-path-text').value;
    var payload = {"file_dir": hdf_file_path};
    hexitec_endpoint.put(payload, 'detector/daq/file_info')
    .then(result => {
        document.querySelector('#hdf-file-path-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#hdf-file-path-warning').innerHTML = error.message;
    });
};

function hdf_file_name_changed()
{
    // Appends timestamp to filename, updates hdf file name
    var hdf_file_name = document.querySelector('#hdf-file-name-text').value;
    var payload = {"file_name": hdf_file_name + "_" + showTime()};
    hexitec_endpoint.put(payload, 'detector/daq/file_info')
    .then(result => {
        document.querySelector('#hdf-file-name-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#hdf-file-name-warning').innerHTML = error.message;
    });
};

function threshold_lower_changed()
{
    var threshold_lower = document.querySelector('#threshold-lower-text').value;
    hexitec_endpoint.put(parseInt(threshold_lower), 'detector/daq/config/summed_image/threshold_lower')
    .then(result => {
        document.querySelector('#threshold-lower-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#threshold-lower-warning').innerHTML = error.message;
    });
};

function threshold_upper_changed()
{
    var threshold_upper = document.querySelector('#threshold-upper-text').value;
    hexitec_endpoint.put(parseInt(threshold_upper), 'detector/daq/config/summed_image/threshold_upper')
    .then(result => {
        document.querySelector('#threshold-upper-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#threshold-upper-warning').innerHTML = error.message;
    });
};

function image_frequency_changed()
{
    var image_frequency = document.querySelector('#image-frequency-text').value;
    hexitec_endpoint.put(parseInt(image_frequency), 'detector/daq/config/summed_image/image_frequency')
    .then(result => {
        document.querySelector('#image-frequency-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#image-frequency-warning').innerHTML = error.message;
    });
};

function hexitec_config_changed()
{
    var hexitec_config = document.querySelector('#hexitec-config-text').value;
    hexitec_endpoint.put({"hexitec_config": hexitec_config}, 'detector/fem/')
    .then(result => {
        document.querySelector('#hexitec-config-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#hexitec-config-warning').innerHTML = error.message;
    });
};

function frames_changed()
{
    var ui_frames = document.querySelector('#frames-text').value;
    hexitec_endpoint.put(Number(ui_frames), 'detector/acquisition/number_frames')
    .then(result => {
        document.querySelector('#frames-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#frames-warning').innerHTML = error.message;
    });
};

function duration_changed()
{
    var duration = document.querySelector('#duration-text').value;
    hexitec_endpoint.put(Number(duration), 'detector/acquisition/duration')
    .then(result => {
        document.querySelector('#duration-warning').innerHTML = "";
        document.getElementById("duration-warning").classList.remove('alert-danger');
    })
    .catch(error => {
        document.querySelector('#duration-warning').innerHTML = error.message;
        document.getElementById("duration-warning").classList.add('alert-danger');
    });
};

function elog_changed()
{
    var entry = document.querySelector('#elog-text').value;
    var payload = {"elog": entry};
    hexitec_endpoint.put(payload, 'detector/status')
    .then(result => {
        // console.log("elog_changed OK");
    })
    .catch(error => {
        console.log("elog: " + error.message);
    });
};

function lv_dataset_changed()
{
    var dataset_name = document.querySelector('#lv_dataset_select').value;
    var payload = {"dataset_name": dataset_name};
    hexitec_endpoint.put(payload, 'detector/daq/config/live_view')
    .then(result => {
        document.querySelector('#lv-dataset-changed-warning').innerHTML = "";
        document.getElementById("lv-dataset-changed-warning").classList.remove('alert-danger');
    })
    .catch(error => {
        document.querySelector('#lv-dataset-changed-warning').innerHTML = error.message;
        document.getElementById("lv-dataset-changed-warning").classList.add('alert-danger');
    });
}

function frame_frequency_changed()
{
    var frame_frequency = document.querySelector('#frame-frequency-text').value;
    hexitec_endpoint.put(parseInt(frame_frequency), 'detector/daq/config/live_view/frame_frequency')
    .then(result => {
        document.querySelector('#frame-frequency-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#frame-frequency-warning').innerHTML = error.message;
    });
};

function per_second_changed()
{
    var per_second = document.querySelector('#per-second-text').value;
    hexitec_endpoint.put(parseInt(per_second), 'detector/daq/config/live_view/per_second')
    .then(result => {
        document.querySelector('#per-second-warning').innerHTML = "";
    })
    .catch(error => {
        document.querySelector('#per-second-warning').innerHTML = error.message;
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
