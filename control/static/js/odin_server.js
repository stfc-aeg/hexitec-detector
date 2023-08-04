const ALERT_ID = {
    'sequencer_info': '#command-sequencer-info-alert',
};

api_version = '0.1';
const hexitec_url = '/api/' + api_version + '/hexitec/';

let hexitec_endpoint;
let last_message_timestamp = '';

// Vars added for Odin-Data
var raw_data_enable = false;
var processed_data_enable = false;
var addition_enable = false;
var discrimination_enable = false;
var next_frame_enable = false;
var calibration_enable = false;
var duration_enable = false;

var polling_thread_running = false;
var system_health = true;
var ui_frames = 10;
var js_not_initialised = true;
var hv_enabled = false;
var software_state = "Unknown";
var odin_cold_initialisation = true;

// Called once, when page 1st loaded
document.addEventListener("DOMContentLoaded", function () {
    hexitec_endpoint = new AdapterEndpoint("hexitec");
    liveview_endpoint = new AdapterEndpoint("live_histogram");
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
    document.querySelector('#environsButton').disable = true;
    // Start polling after page loaded (800 ms)
    setTimeout(function () {
        if (polling_thread_running === false) {
            polling_thread_running = true;
            start_polling_thread();
        }
    }, 800);
});

// Apply UI configuration choices
function applyButtonClicked() {
    apply_ui_values();
}

function applyButton2Clicked() {
    apply_ui_values();
}

function connectButtonClicked() {
    // On cold initialisation: configure FP, wait 800 ms before connecting
    //  Any subsequent time: Do not configure FP, connect straightaway
    let time_delay = 0;
    if (odin_cold_initialisation) {
        commit_configuration();
        hexitec_config_changed();
        time_delay = 800;
    }
    setTimeout(function () {
        connect_hardware();
    }, time_delay);
}

function hvOnButtonClicked() {
    // TODO: Switch HV on
    hv_enabled = true;
    document.querySelector('#hvOnButton').disabled = true;
    document.querySelector('#hvOffButton').disabled = false;
    hv_on();
}

function hvOffButtonClicked() {
    // TODO: Switch HV off
    hv_enabled = false;
    document.querySelector('#hvOnButton').disabled = false;
    document.querySelector('#hvOffButton').disabled = true;
    hv_off();
}

function environsButtonClicked() {
    hexitec_endpoint.put({ "environs": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function initialiseButtonClicked() {
    initialise_hardware();
}

function offsetsButtonClicked() {
    collect_offsets();
}

function acquireButtonClicked() {
    collect_data();
}

function cancelButtonClicked() {
    cancel_data();
}

function resetButtonClicked() {
    reset_error();
}

function disconnectButtonClicked() {
    disconnect_hardware();
}

function saveOdinClicked() {
    save_odin();
}

function loadOdinClicked() {
    load_odin();
    js_not_initialised = true;
}

// Set Charged Sharing selection, supporting function
function setCSSelection(value) {
    addition_enable = false;
    discrimination_enable = false;
    // Define colours to note which button is selected, and which buttons are unselected
    selected = '#0000FF';
    unselected = '#337ab7';
    switch (value) {
        case "None":
            document.getElementById("noneButton").style.backgroundColor = selected;
            document.getElementById("addButton").style.backgroundColor = unselected;
            document.getElementById("disButton").style.backgroundColor = unselected;
            break;
        case "Add":
            document.getElementById("noneButton").style.backgroundColor = unselected;
            document.getElementById("addButton").style.backgroundColor = selected;
            document.getElementById("disButton").style.backgroundColor = unselected;
            addition_enable = true;
            break;
        case "Dis":
            document.getElementById("noneButton").style.backgroundColor = unselected;
            document.getElementById("addButton").style.backgroundColor = unselected;
            document.getElementById("disButton").style.backgroundColor = selected;
            discrimination_enable = true;
            break;
        default:
            console.log("You must have added a fourth button, Neither None/Add/Dis pressed");
            document.querySelector('#odin-control-error').innerHTML = "setCSSelection: " + error.message;
            break;
    }
}

// HTML callback function selecting Charged Sharing algorithm (none/add/dis Buttons)
function setCS(e) {
    let target = e.target;
    setCSSelection(target.value);

    var pixel_grid_size = document.querySelector('#pixel-grid-size-text').value;

    var addition_payload = {
        "addition":
        {
            "enable": addition_enable,
            "pixel_grid_size": parseInt(pixel_grid_size)
        }
    };

    var discrimination_payload = {
        "discrimination":
        {
            "enable": discrimination_enable,
            "pixel_grid_size": parseInt(pixel_grid_size)
        }
    };

    hexitec_endpoint.put(addition_payload, 'detector/daq/config')
        .catch(error => {
            console.log("FAILED to update Addition: " + error.message);
        });

    hexitec_endpoint.put(discrimination_payload, 'detector/daq/config')
        .catch(error => {
            console.log("FAILED to update Discrimination: " + error.message);
        });
}

function start_polling_thread() {
    // Starts the polling thread ferrying information from Odin to the UI
    poll_fem();
}

function toggle_ui_elements(bBool) {
    document.querySelector('#initialiseButton').disabled = bBool;
    document.querySelector('#acquireButton').disabled = bBool;
    document.querySelector('#cancelButton').disabled = bBool;
    if (hv_enabled)
        document.querySelector('#hvOffButton').disabled = bBool;
    else
        document.querySelector('#hvOnButton').disabled = bBool;
    document.querySelector('#environsButton').disabled = bBool;
    document.querySelector('#offsetsButton').disabled = bBool;
    document.querySelector('#applyButton').disabled = bBool;
    document.querySelector('#applyButton2').disabled = bBool;
    document.querySelector('#hdf-file-path-text').disabled = bBool;
    document.querySelector('#hdf-file-name-text').disabled = bBool;
    document.querySelector('#hexitec-config-text').disabled = bBool;
}

function poll_fem() {
    // Check whether odin_server is running
    hexitec_endpoint.get_url(hexitec_url + 'detector')
        .then(result => {
            display_log_messages();
            // Clear any previous error
            document.querySelector('#odin-control-error').innerHTML = "";
            software_state = result["detector"]["software_state"];
            odin_cold_initialisation = result["detector"]["cold_initialisation"];

            // If javascript isn't initialised, populate UI with Odin's settings
            if (js_not_initialised) {
                load_odin();
                update_ui_with_odin_settings();
                js_not_initialised = false;
            }

            // Odin running, commence polling

            // Polls the fem(s) for hardware status, environmental data, etc
            hexitec_endpoint.get_url(hexitec_url + 'fr/status/')
                .then(result => {
                    var numNodes = result["value"].length;
                    for (var i = 0; i < numNodes; i++) {
                        const frames = result["value"][i].frames;
                        const decoder = result["value"][i].decoder;
                        const buffers = result["value"][i].buffers;
                        document.querySelector('#frames_received' + i).innerHTML = frames.received;
                        document.querySelector('#frames_released' + i).innerHTML = frames.released;
                        document.querySelector('#frames_dropped' + i).innerHTML = frames.dropped;
                        document.querySelector('#frames_timedout' + i).innerHTML = frames.timedout;

                        document.querySelector('#fem_packets_lost' + i).innerHTML = decoder.fem_packets_lost;
                        document.querySelector('#packets_lost' + i).innerHTML = decoder.packets_lost;
                        document.querySelector('#buffers_empty' + i).innerHTML = buffers.empty;
                        document.querySelector('#buffers_mapped' + i).innerHTML = buffers.mapped;
                    }
                })
                .catch(error => {
                    document.querySelector('#odin-control-error').innerHTML = "Polling FR: " + error.message;
                });

            // Polls Proxy adapter for leak detector information
            hexitec_endpoint.get_url('/api/' + api_version + '/proxy/')
                .then(result => {
                    var results = result["value"];
                    var system = result["leak"]["system"];
                    var outlets = system["outlets"];
                    var packet_info = result["leak"]["system"]["packet_info"];
                    var ld_warning = packet_info["warning"];

                    // Expand leak detector parameter coverage

                    // Update GUI
                    var ld_fault = JSON.stringify(packet_info["fault"], null, 4);
                    var ld_chiller_state = outlets["chiller"]["state"];
                    var ld_chiller_enable = outlets["chiller"]["enabled"];
                    var ld_daq_state = outlets["daq"]["state"];
                    var ld_daq_enable = outlets["daq"]["enabled"];

                    document.querySelector('#ld_warning').innerHTML = ld_warning;
                    document.querySelector('#ld_fault').innerHTML = ld_fault;
                    document.querySelector('#ld_chiller_state').innerHTML = ld_chiller_state;
                    document.querySelector('#ld_chiller_enabled').innerHTML = ld_chiller_enable;
                    document.querySelector('#ld_daq_enabled').innerHTML = ld_daq_enable;
                    document.querySelector('#ld_daq_state').innerHTML = ld_daq_state;

                    if (ld_chiller_state === true) {
                        document.querySelector('#ld_chiller_control_radio1').checked = true;    // Enables
                    }
                    else {
                        document.querySelector('#ld_chiller_control_radio2').checked = true;    // Disables
                    }
        
                    if (ld_daq_state === true) {
                        document.querySelector('#ld_DAQ_control_radio1').checked = true;    // Enables
                    }
                    else {
                        document.querySelector('#ld_DAQ_control_radio2').checked = true;    // Disables
                    }

                })
                .catch(error => {
                    document.querySelector('#odin-control-error').innerHTML = "Polling Leak: " + error.message;
                });

            // http://localhost:8888/api/0.1/hexitec/fp/status/error/2
            // Polls the fem for hardware status, environmental data, etc
            hexitec_endpoint.get_url(hexitec_url + 'fp/status/')
                .then(result => {
                    // // Print all errors reported by one FP:
                    // console.log("    [val][1].error: " + JSON.stringify(result["value"][1].error, null, 4));
                    var numNodes = result["value"].length;
                    for (var i = 0; i < numNodes; i++) {
                        // Print all error(s) belonging to specified node:
                        // console.log( i + " results: " + result["value"][i].error);
                        if (result["value"][i].error === undefined) {
                            // Current node not configured, clear any previous error(s)
                            document.querySelector('#fp_errors' + i).innerHTML = 0;
                        }
                        else {
                            var numErrors = result["value"][i].error.length;
                            document.querySelector('#fp_errors' + i).innerHTML = numErrors;
                            for (var j = 0; j < numErrors; j++) {
                                // Report all nodes error(s)
                                // console.log(" Node" + i + ", Err" + j + " : " + result["value"][i].error[j]);
                            }
                        }
                    }
                })
                .catch(error => {
                    document.querySelector('#odin-control-error').innerHTML = "Polling FP: " + error.message;
                });

            hexitec_endpoint.get_url(hexitec_url + 'detector')
                .then(result => {
                    const fem = result["detector"]["fem"]
                    const adapter_status = result["detector"]["status"] // adapter.py's status
                    document.querySelector('#all_data_sent').innerHTML = fem["all_data_sent"];
                    const hardware_connected = fem["hardware_connected"];
                    const hardware_busy = fem["hardware_busy"];

                    const daq_in_progress = result["detector"]["daq"]["status"]["in_progress"];

                    const frames_expected = result["detector"]["daq"]["status"]["frames_expected"];
                    const frames_received = result["detector"]["daq"]["status"]["frames_received"];
                    const frames_processed = result["detector"]["daq"]["status"]["frames_processed"];
                    const processed_remaining = result["detector"]["daq"]["status"]["processed_remaining"];
                    const received_remaining = result["detector"]["daq"]["status"]["received_remaining"];
                    const fraction_received = (frames_received / frames_expected).toFixed(2);
                    const fraction_processed = (frames_processed / frames_expected).toFixed(2);
                    // console.log(" rxd: " + frames_received + " " + received_remaining + " (" + fraction_received + ")" +
                    //         " proc'd: " + frames_processed + " " + processed_remaining + " (" + fraction_processed + ")" +
                    //         " tot: " + frames_expected);    /// DEBUGGING
                    var daq_progress = document.getElementById("daq-progress");
                    daq_progress.value = fraction_received * 100;
                    var processing_progress = document.getElementById("processing-progress");
                    processing_progress.value = fraction_processed * 100;

                    // Enable buttons when connection completed
                    if (hardware_connected === true) {
                        // Disable connect, enable disconnect button
                        document.querySelector('#disconnectButton').disabled = false;
                        document.querySelector('#connectButton').disabled = true;
                        if (hardware_busy === true) {
                            toggle_ui_elements(true);   // Disable UI elements
                        }
                        else {
                            toggle_ui_elements(false);  // Enable UI elements
                            // Disable Environs button if collecting environmental data
                            if (fem["environs_in_progress"] === true)
                                document.querySelector('#environsButton').disabled = true;
                            else
                                document.querySelector('#environsButton').disabled = false;
                        }
                        if (daq_in_progress === true) {
                            // Enable cancelButton but disable changing file[path]
                            document.querySelector('#cancelButton').disabled = false;
                            document.querySelector('#hdf-file-path-text').disabled = true;
                            document.querySelector('#hdf-file-name-text').disabled = true;
                        }
                        else {
                            // Disable cancelButton but enable changing file[path]
                            document.querySelector('#cancelButton').disabled = true;
                            document.querySelector('#hdf-file-path-text').disabled = false;
                            document.querySelector('#hdf-file-name-text').disabled = false;
                        }
                    }
                    else {
                        document.querySelector('#disconnectButton').disabled = true;
                        document.querySelector('#connectButton').disabled = false;
                        document.querySelector('#initialiseButton').disabled = true;
                        document.querySelector('#acquireButton').disabled = true;
                        document.querySelector('#cancelButton').disabled = true;
                        if (hv_enabled)
                            document.querySelector('#hvOffButton').disabled = true;
                        else
                            document.querySelector('#hvOnButton').disabled = true;
                        document.querySelector('#environsButton').disabled = true;
                        document.querySelector('#offsetsButton').disabled = true;

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

                    // console.log(hardware_busy + " " + daq_in_progress + 
                    //             " <= hw_busy, daq_in_prog " + "   %_compl: "
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

                    const offsets_timestamp = fem["offsets_timestamp"];
                    document.querySelector('#offsets_ts').innerHTML = offsets_timestamp

                    // Obtain overall adapter(.py's) status

                    var status_message = adapter_status["status_message"];
                    document.querySelector('#odin-control-message').innerHTML = status_message;

                    // Get adapter error (if set)
                    const status_error = adapter_status["status_error"];
                    if (status_error.length > 0) {
                        const status = "Error: '" + status_error + "'";
                        document.querySelector('#odin-control-error').innerHTML = status;
                    }

                    // Update VSRs sensor data (plus sync status)
                    var numVSRs = fem["vsr_humidity_list"].length;
                    let idx = 0;
                    for (var i = 0; i < numVSRs; i++) {
                        idx = i + 1;
                        // console.log("       [" + i + "] = " + fem['vsr_humidity_list'][i]);
                        document.querySelector('#vsr' + idx + '_humidity').innerHTML = fem["vsr_humidity_list"][i].toFixed(2);
                        document.querySelector('#vsr' + idx + '_ambient').innerHTML = fem["vsr_ambient_list"][i].toFixed(2);
                        document.querySelector('#vsr' + idx + '_asic1').innerHTML = fem["vsr_asic1_list"][i].toFixed(2);
                        document.querySelector('#vsr' + idx + '_asic2').innerHTML = fem["vsr_asic2_list"][i].toFixed(2);
                        document.querySelector('#vsr' + idx + '_adc').innerHTML = fem["vsr_adc_list"][i].toFixed(2);
                        document.querySelector('#vsr' + idx + '_hv').innerHTML = fem["vsr_hv_list"][i].toFixed(2);
                        document.querySelector('#vsr' + idx + '_sync').innerHTML = fem["vsr_sync_list"][i];
                    }
                    /// To be implemented: system_health - true=fem OK, false=fem bad

                    // Traffic "light" green/red to indicate system good/bad

                    lampDOM = document.getElementById("Green");

                    // Clear status if camera disconnected, otherwise look for any error
                    if (status_message === "Camera disconnected") {
                        lampDOM.classList.remove("lampGreen");
                        lampDOM.classList.remove("lampRed");
                    }
                    else {
                        if (status_error.length === 0) {
                            lampDOM.classList.add("lampGreen");
                        }
                        else {
                            lampDOM.classList.remove("lampGreen");
                            lampDOM.classList.add("lampRed");
                        }
                    }
                })
                .catch(error => {
                    document.querySelector('#odin-control-error').innerHTML = "Polling Detector: " + error.message;
                });
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = "Odin_server unreachable";
        });
    if (polling_thread_running === true) {
        window.setTimeout(poll_fem, 850);
    }
}

function connect_hardware() {
    hexitec_endpoint.put({ "connect_hardware": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function hv_on() {
    hexitec_endpoint.put({ "hv_on": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function hv_off() {
    hexitec_endpoint.put({ "hv_off": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function initialise_hardware() {
    hexitec_endpoint.put({ "initialise_hardware": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function collect_offsets() {
    // Collects offsets used for dark corrections in subsequent acquisitions
    hexitec_endpoint.put({ "collect_offsets": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function collect_data() {
    hexitec_endpoint.put({ "start_acq": "" }, 'detector/acquisition')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function cancel_data() {
    hexitec_endpoint.put({ "stop_acq": "" }, 'detector/acquisition')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function reset_error() {
    hexitec_endpoint.put({ "reset_error": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function disconnect_hardware() {
    hexitec_endpoint.put({ "disconnect_hardware": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

function save_odin() {
    saveOdinButton = document.querySelector('#saveOdinButton');
    hexitec_endpoint.put({ "save_odin": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
            saveOdinButton.classList.remove('alert-danger');
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
            saveOdinButton.setCustomValidity(error.message);
            saveOdinButton.reportValidity();
            saveOdinButton.classList.add('alert-danger');
        });
}

function load_odin() {
    loadOdinButton = document.querySelector('#loadOdinButton');
    hexitec_endpoint.put({ "load_odin": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
            loadOdinButton.classList.remove('alert-danger');
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
            loadOdinButton.setCustomValidity(error.message);
            loadOdinButton.reportValidity();
            loadOdinButton.classList.add('alert-danger');
        });
}

function commit_configuration() {
    hexitec_endpoint.put({ "commit_configuration": "" }, 'detector')
        .then(result => {
            document.querySelector('#odin-control-error').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#odin-control-error').innerHTML = error.message;
        });
}

// apply_ui_values: Disconnect existing sequence of plugins, 
//  load the sequence of plugins corresponding to UI settings
function apply_ui_values() {
    // Load all UI settings into HexitecDAQ's ParameterTree

    // Generate temporary config file(s) loading plugins chain,
    //  push HexitecDAQ's ParameterTree settings to FP's plugins
    commit_configuration();

    // Read configuration file into memory, recalculate frame_rate
    hexitec_config_changed();

    // This will be executed after however many milliseconds 
    //  specified at the end of this function definition
    setTimeout(function () {

        // Delay necessary otherwise some plugins' variables are configured 
        // before they are actually loaded (which will not work obviously)

        changeRawDataEnable();
        changeProcessedDataEnable();
        threshold_mode_changed();
        threshold_value_changed();
        threshold_filename_changed();
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

function threshold_filename_changed() {
    // Update threshold filename if threshold filename mode set
    //  (0: strings equal [filename mode], 1: not [none/value mode])
    var threshold_mode = document.querySelector('#threshold-mode-text').value;
    if (threshold_mode.localeCompare("filename") === 0) {
        var threshold_filename = document.querySelector('#threshold-filename-text');
        hexitec_endpoint.put(threshold_filename.value, 'detector/daq/config/threshold/threshold_filename')
            .then(result => {
                threshold_filename.classList.remove('alert-danger');
            })
            .catch(error => {
                threshold_filename.setCustomValidity(error.message);
                threshold_filename.reportValidity();
                threshold_filename.classList.add('alert-danger');
            });
    }
}

function threshold_value_changed() {
    var threshold_value = document.querySelector('#threshold-value-text');
    hexitec_endpoint.put(parseInt(threshold_value.value), 'detector/daq/config/threshold/threshold_value')
        .then(result => {
            threshold_value.classList.remove('alert-danger');
        })
        .catch(error => {
            threshold_value.setCustomValidity(error.message);
            threshold_value.reportValidity();
            threshold_value.classList.add('alert-danger');
        });
}

function threshold_mode_changed() {
    var threshold_mode = document.querySelector('#threshold-mode-text').value;
    hexitec_endpoint.put(threshold_mode, 'detector/daq/config/threshold/threshold_mode')
        .then(result => {
            document.querySelector('#threshold-mode-warning').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#threshold-mode-warning').innerHTML = error.message;
        });
    threshold_filename_changed();
}

function gradients_filename_changed() {
    // Only check/update gradients filename if calibration is enabled
    if (calibration_enable === true) {
        var gradients_filename = document.querySelector('#gradients-filename-text');
        hexitec_endpoint.put(gradients_filename.value, 'detector/daq/config/calibration/gradients_filename')
            .then(result => {
                gradients_filename.classList.remove('alert-danger');
            })
            .catch(error => {
                gradients_filename.setCustomValidity(error.message);
                gradients_filename.reportValidity();
                gradients_filename.classList.add('alert-danger');
            });
    }
}

function intercepts_filename_changed() {
    // Only check/update intercepts filename if calibration is enabled
    if (calibration_enable === true) {
        var intercepts_filename = document.querySelector('#intercepts-filename-text');
        hexitec_endpoint.put(intercepts_filename.value, 'detector/daq/config/calibration/intercepts_filename')
            .then(result => {
                intercepts_filename.classList.remove('alert-danger');
            })
            .catch(error => {
                intercepts_filename.setCustomValidity(error.message);
                intercepts_filename.reportValidity();
                intercepts_filename.classList.add('alert-danger');
            });
    }
}

function pixel_grid_size_changed() {
    var pixel_grid_size = document.querySelector('#pixel-grid-size-text');

    hexitec_endpoint.put(parseInt(pixel_grid_size.value), 'detector/daq/config/addition/pixel_grid_size')
        .then(result => {
            pixel_grid_size.classList.remove('alert-danger');
        })
        .catch(error => {
            pixel_grid_size.setCustomValidity(error.message);
            pixel_grid_size.reportValidity();
            pixel_grid_size.classList.add('alert-danger');
        });

    hexitec_endpoint.put(parseInt(pixel_grid_size.value), 'detector/daq/config/discrimination/pixel_grid_size')
        .then(result => {
            pixel_grid_size.classList.remove('alert-danger');
        })
        .catch(error => {
            pixel_grid_size.setCustomValidity(error.message);
            pixel_grid_size.reportValidity();
            pixel_grid_size.classList.add('alert-danger');
        });
}

function bin_start_changed() {
    var bin_start = document.querySelector('#bin-start-text');
    hexitec_endpoint.put(parseInt(bin_start.value), 'detector/daq/config/histogram/bin_start')
        .then(result => {
            bin_start.classList.remove('alert-danger');
        })
        .catch(error => {
            bin_start.setCustomValidity(error.message);
            bin_start.reportValidity();
            bin_start.classList.add('alert-danger');
        });
    // Support histogram (1D) Live view data
    liveview_endpoint.put(parseFloat(bin_start.value), 'bin_start')
        .catch(error => {
            console.log("Couldn't update bin_start");
        });
}

function bin_end_changed() {
    var bin_end = document.querySelector('#bin-end-text');
    hexitec_endpoint.put(parseInt(bin_end.value), 'detector/daq/config/histogram/bin_end')
        .then(result => {
            bin_end.classList.remove('alert-danger');
        })
        .catch(error => {
            bin_end.setCustomValidity(error.message);
            bin_end.reportValidity();
            bin_end.classList.add('alert-danger');
        });
    // Support histogram (1D) Live view data
    liveview_endpoint.put(parseFloat(bin_end.value), 'bin_end')
        .catch(error => {
            console.log("Couldn't update bin_end");
        });
}

function bin_width_changed() {
    var bin_width = document.querySelector('#bin-width-text');
    hexitec_endpoint.put(parseFloat(bin_width.value), 'detector/daq/config/histogram/bin_width')
        .then(result => {
            bin_width.classList.remove('alert-danger');
        })
        .catch(error => {
            bin_width.setCustomValidity(error.message);
            bin_width.reportValidity();
            bin_width.classList.add('alert-danger');
        });
    // Support histogram (1D) Live view data
    liveview_endpoint.put(parseFloat(bin_width.value), 'bin_width')
        .catch(error => {
            console.log("Couldn't update bin_width");
        });
}

// Change (Duration) mode, true if Seconds selected, false = Frames selected
function changeModeEnable() {
    duration_enable = document.getElementById('mode_radio1').checked;

    hexitec_endpoint.put(duration_enable, 'detector/acquisition/duration_enable')
        .catch(error => {
            console.log("duration enable: couldn't be changed: " + error.message);
        });
    configure_duration(duration_enable);
};

// Helper function, configures duration/frames according to selection
function configure_duration(duration_enable) {
    if (duration_enable) {
        document.querySelector('#duration-text').disabled = false;
        document.querySelector('#frames-text').disabled = true;
        duration_changed();
    }
    else {
        document.querySelector('#duration-text').disabled = true;
        document.querySelector('#frames-text').disabled = false;
        frames_changed();
    }
};

function changeProcessedDataEnable() {
    // Odin Control do not support bool, must target FP and DAQ adapter
    processed_data_enable = document.getElementById('processed_data_radio1').checked;

    processed_data_enable = JSON.stringify(processed_data_enable);
    processed_data_enable = (processed_data_enable === "true");
    hexitec_endpoint.put(processed_data_enable, 'fp/config/histogram/pass_processed')
        .catch(error => {
            console.log("Processed dataset in FP: couldn't be changed: " + errorr.message);
        });

    hexitec_endpoint.put(processed_data_enable, 'detector/daq/config/histogram/pass_processed')
        .catch(error => {
            console.log("Processed dataset in daq: couldn't be changed: " + error.message);
        });
};

function changeRawDataEnable() {
    // Odin Control do not support bool, must target FP and DAQ adapter
    raw_data_enable = document.getElementById('raw_data_radio1').checked;

    raw_data_enable = JSON.stringify(raw_data_enable);
    raw_data_enable = (raw_data_enable === "true");
    hexitec_endpoint.put(raw_data_enable, 'fp/config/histogram/pass_raw')
        .catch(error => {
            console.log("Raw dataset in FP: couldn't be changed: " + error.message);
        });

    hexitec_endpoint.put(raw_data_enable, 'detector/daq/config/histogram/pass_raw')
        .catch(error => {
            console.log("Raw dataset in daq: couldn't be changed: " + error.message);
        });
};

function changeNextFrameEnable() {
    next_frame_enable = document.getElementById('next_frame_radio1').checked;
    next_frame_enable = JSON.stringify(next_frame_enable);
    next_frame_enable = (next_frame_enable === "true");
    hexitec_endpoint.put(next_frame_enable, 'detector/daq/config/next_frame/enable')
        .catch(error => {
            console.log("Next Frame couldn't be changed: " + error.message);
        });
};

function changeChillerEnable() {
    ld_chiller_enable = document.getElementById('ld_chiller_control_radio1').checked;
    ld_chiller_enable = JSON.stringify(ld_chiller_enable);
   

    hexitec_endpoint.put_url(ld_chiller_enable, 'api/' + api_version + '/proxy/leak/system/outlets/chiller/state')
        .catch(error => {
            console.log("LD CHILLER Enable: couldn't be changed: " + error.message);
        });
};

function changeDAQEnable() {
    ld_DAQ_enable = document.getElementById("ld_DAQ_control_radio1").checked;
    ld_DAQ_enable = JSON.stringify(ld_DAQ_enable);


    hexitec_endpoint.put_url(ld_DAQ_enable, "api/" + api_version + '/proxy/leak/system/outlets/daq/state')
        .catch(error => {
            console.log("LD DAQ has error:" + error.message)
            console.log(ld_DAQ_enable);
        });
}

// Function only ever called from HTML page
function changeCalibrationEnable() {
    calibration_enable = document.getElementById('calibration_radio1').checked;
    calibration_enable = JSON.stringify(calibration_enable);
    calibration_enable = (calibration_enable === "true");
    configure_bin_labels(calibration_enable);
    if (calibration_enable) {
        document.querySelector('#bin-start-text').value = 0;
        document.querySelector('#bin-end-text').value = 200;
        document.querySelector('#bin-width-text').value = 0.25;
    }
    else {
        document.querySelector('#bin-start-text').value = 0;
        document.querySelector('#bin-end-text').value = 8000;
        document.querySelector('#bin-width-text').value = 10;
    }

    hexitec_endpoint.put(calibration_enable, 'detector/daq/config/calibration/enable')
        .catch(error => {
            console.log("calibration_enable failed: " + error.message);
        });

    // If calibration now enabled, check coefficients files are valid
    if (calibration_enable) {
        gradients_filename_changed();
        intercepts_filename_changed()
    }
};

// Helper function, configures histogram bin labels according to calibration setting
function configure_bin_labels(calibration_enable) {
    if (calibration_enable) {
        document.querySelector('#bin_start').innerHTML = "Bin Start: [keV]&nbsp;";
        document.querySelector('#bin_end').innerHTML = "Bin End: [keV]&nbsp;";
        document.querySelector('#bin_width').innerHTML = "Bin Width: [keV]&nbsp;";
    }
    else {
        document.querySelector('#bin_start').innerHTML = "Bin Start: [ADU]&nbsp;";
        document.querySelector('#bin_end').innerHTML = "Bin End: [ADU]&nbsp;";
        document.querySelector('#bin_width').innerHTML = "Bin Width: [ADU]&nbsp;";
    }
}

function sensorsLayoutChange(sensors_layout) {
    // Sets hardware sensors Configuration; i.e. number of rows and columns of sensors
    hexitec_endpoint.put({ "sensors_layout": sensors_layout }, 'detector/daq')
        .then(result => {
            document.querySelector('#sensors-layout-warning').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#sensors-layout-warning').innerHTML = error.message;
        });
}

function numberNodesChange(number_nodes) {
    // Sets number of FR/FP (pair of) nodes
    hexitec_endpoint.put(parseInt(number_nodes), 'detector/status/number_nodes')
        .then(result => {
            document.querySelector('#number-nodes-warning').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#number-nodes-warning').innerHTML = error.message;
        });
}

function compressionChange(compression) {
    // Sets compression on (blosc) or off (none)
    hexitec_endpoint.put({ "compression_type": compression }, 'detector/daq')
        .then(result => {
            document.querySelector('#compression-warning').innerHTML = "";
        })
        .catch(error => {
            document.querySelector('#compression-warning').innerHTML = error.message;
        });
}

function hdf_file_path_changed() {
    var hdf_file_path = document.querySelector('#hdf-file-path-text');
    var payload = { "file_dir": hdf_file_path.value };
    hexitec_endpoint.put(payload, 'detector/daq/file_info')
        .then(result => {
            hdf_file_path.classList.remove('alert-danger');
        })
        .catch(error => {
            hdf_file_path.setCustomValidity(error.message);
            hdf_file_path.reportValidity();
            hdf_file_path.classList.add('alert-danger');
        });
};

function hdf_file_name_changed() {
    // (Don't) Append timestamp to filename, update hdf file name
    var hdf_file_name = document.querySelector('#hdf-file-name-text');
    var payload = { "file_name": hdf_file_name.value }; // + "_" + showTime()};
    hexitec_endpoint.put(payload, 'detector/daq/file_info')
        .then(result => {
            hdf_file_name.classList.remove('alert-danger');
        })
        .catch(error => {
            hdf_file_name.setCustomValidity(error.message);
            hdf_file_name.reportValidity();
            hdf_file_name.classList.add('alert-danger');
        });
};

function threshold_lower_changed() {
    var threshold_lower = document.querySelector('#threshold-lower-text');
    hexitec_endpoint.put(parseInt(threshold_lower.value), 'detector/daq/config/summed_image/threshold_lower')
        .then(result => {
            threshold_lower.classList.remove('alert-danger');
        })
        .catch(error => {
            threshold_lower.setCustomValidity(error.message);
            threshold_lower.reportValidity();
            threshold_lower.classList.add('alert-danger');
        });
};

function threshold_upper_changed() {
    var threshold_upper = document.querySelector('#threshold-upper-text');
    hexitec_endpoint.put(parseInt(threshold_upper.value), 'detector/daq/config/summed_image/threshold_upper')
        .then(result => {
            threshold_upper.classList.remove('alert-danger');
        })
        .catch(error => {
            threshold_upper.setCustomValidity(error.message);
            threshold_upper.reportValidity();
            threshold_upper.classList.add('alert-danger');
        });
};

function image_frequency_changed() {
    var image_frequency = document.querySelector('#image-frequency-text');
    hexitec_endpoint.put(parseInt(image_frequency.value), 'detector/daq/config/summed_image/image_frequency')
        .then(result => {
            image_frequency.classList.remove('alert-danger');
        })
        .catch(error => {
            image_frequency.setCustomValidity(error.message);
            image_frequency.reportValidity();
            image_frequency.classList.add('alert-danger');
        });
};

function hexitec_config_changed() {
    var hexitec_config = document.querySelector('#hexitec-config-text');
    hexitec_endpoint.put({ "hexitec_config": hexitec_config.value }, 'detector/fem/')
        .then(result => {
            hexitec_config.classList.remove('alert-danger');
        })
        .catch(error => {
            hexitec_config.setCustomValidity(error.message);
            hexitec_config.reportValidity();
            hexitec_config.classList.add('alert-danger');
        });
};

function frames_changed() {
    ui_frames = document.querySelector('#frames-text');
    hexitec_endpoint.put(Number(ui_frames.value), 'detector/acquisition/number_frames')
        .then(result => {
            ui_frames.classList.remove('alert-danger');
        })
        .catch(error => {
            ui_frames.setCustomValidity(error.message);
            ui_frames.reportValidity();
            ui_frames.classList.add('alert-danger');
        });
};

function duration_changed() {
    var duration = document.querySelector('#duration-text');
    hexitec_endpoint.put(Number(duration.value), 'detector/acquisition/duration')
        .then(result => {
            duration.classList.remove('alert-danger');
        })
        .catch(error => {
            duration.setCustomValidity(error.message);
            duration.reportValidity();
            duration.classList.add('alert-danger');
        });
};

function elog_changed() {
    var entry = document.querySelector('#elog-text');
    var payload = { "elog": entry.value };
    hexitec_endpoint.put(payload, 'detector/status')
        .then(result => {
            entry.classList.remove('alert-danger');
        })
        .catch(error => {
            entry.setCustomValidity(error.message);
            entry.reportValidity();
            entry.classList.add('alert-danger');
        });
};

function lv_dataset_changed() {
    var dataset_name = document.querySelector('#lv_dataset_select').value;
    var payload = { "dataset_name": dataset_name };
    hexitec_endpoint.put(payload, 'detector/daq/config/lvframes')
        .then(result => {
            document.querySelector('#lv-dataset-changed-warning').innerHTML = "";
            document.getElementById("lv-dataset-changed-warning").classList.remove('alert-danger');
        })
        .catch(error => {
            document.querySelector('#lv-dataset-changed-warning').innerHTML = error.message;
            document.getElementById("lv-dataset-changed-warning").classList.add('alert-danger');
        });
}

function update_ui_with_odin_settings() {
    hexitec_endpoint.get_url('/api/' + api_version + '/proxy/')
        .then(result => {
            // Update GUI with leak detector information
            var results = result["value"];
            var system = result["leak"]["system"];
            var outlets = system["outlets"];
            var packet_info = result["leak"]["system"]["packet_info"];
            var ld_warning = packet_info["warning"];


            var ld_chiller_state = outlets["chiller"]["state"];
            var ld_chiller_enable = outlets["chiller"]["enabled"];
            var ld_daq_state = outlets["daq"]["state"];
            var ld_daq_enable = outlets["chiller"]["enabled"];

            var ld_warning = packet_info["warning"];

            document.querySelector('#ld_daq_state').innerHTML = ld_daq_state;
            document.querySelector('#ld_warning').innerHTML = ld_warning;
            document.querySelector('#ld_fault').innerHTML = ld_fault;
            document.querySelector('#ld_chiller_state').innerHTML = ld_chiller_state;
            document.querySelector('#ld_chiller_enabled').innerHTML = ld_chiller_enable;
            document.querySelector('#ld_daq_enabled').innerHTML = ld_daq_enable;


            // Expand leak detector parameter coverage

            if (ld_chiller_state === true) {
                document.querySelector('#ld_chiller_control_radio1').checked = true;    // Enables
            }
            else {
                document.querySelector('#ld_chiller_control_radio2').checked = true;    // Disables
            }

            if (ld_daq_state === true) {
                document.querySelector('#ld_DAQ_control_radio1').checked = true;    // Enables
            }
            else {
                document.querySelector('#ld_DAQ_control_radio2').checked = true;    // Disables
            }

        })
        .catch(error => {
            console.log("update_ui_with_odin_settings() ERROR: " + error.message);
        });

    hexitec_endpoint.get_url(hexitec_url + 'detector')
        .then(result => {
            const daq_config = result["detector"]["daq"]["config"];
            // Update CS selections
            var selection = "None";
            var pixel_grid_size = 3;
            if (daq_config.addition.enable === true) {
                selection = "Add";
                pixel_grid_size = daq_config.addition.pixel_grid_size;
            }
            else if (daq_config.discrimination.enable === true) {
                selection = "Dis";
                pixel_grid_size = daq_config.discrimination.pixel_grid_size;
            }
            setCSSelection(selection);
            document.querySelector('#pixel-grid-size-text').value = pixel_grid_size;

            // Update Threshold
            const threshold_mode = daq_config.threshold.threshold_mode;
            // Reduce absolute path: /abs/path/to/hexitec/hexitec-detector/data/config/t_threshold_file.txt
            // to the relative path: data/config/t_threshold_file.txt
            const abs_path = daq_config.threshold.threshold_filename;
            const threshold_filename = abs_path.substring(abs_path.search("data/"));
            const threshold_value = daq_config.threshold.threshold_value;
            document.querySelector('#threshold-mode-text').value = threshold_mode;
            document.querySelector('#threshold-filename-text').value = threshold_filename;
            document.querySelector('#threshold-value-text').value = threshold_value;

            // Updated Gradients, Intercepts files
            const abs_gradients = daq_config.calibration.gradients_filename;
            const gradients_filename = abs_gradients.substring(abs_gradients.search("data/"));
            const abs_intercepts = daq_config.calibration.intercepts_filename;
            const intercepts_filename = abs_intercepts.substring(abs_intercepts.search("data/"));
            document.querySelector('#gradients-filename-text').value = gradients_filename;
            document.querySelector('#intercepts-filename-text').value = intercepts_filename;

            const bin_start = daq_config.histogram.bin_start;
            const bin_end = daq_config.histogram.bin_end;
            const bin_width = daq_config.histogram.bin_width;
            document.querySelector('#bin-start-text').value = bin_start;
            document.querySelector('#bin-end-text').value = bin_end;
            document.querySelector('#bin-width-text').value = bin_width;

            const acquisition = result["detector"]["acquisition"];

            const duration = acquisition.duration;
            document.querySelector('#duration-text').value = duration;
            const frames = acquisition.number_frames;
            document.querySelector('#frames-text').value = frames;

            duration_enable = acquisition.duration_enable;
            if (duration_enable === true) {
                document.querySelector('#mode_radio1').checked = true;	// Seconds
            }
            else {
                document.querySelector('#mode_radio2').checked = true;	// Frames
            }
            configure_duration(duration_enable);

            const processed_dataset = daq_config.histogram.pass_processed;
            if (processed_dataset === true) {
                document.querySelector('#processed_data_radio1').checked = true;    // Enables processing Dataset
            }
            else {
                document.querySelector('#processed_data_radio2').checked = true;    // Disables processing dataset
            }

            const raw_dataset = daq_config.histogram.pass_raw;
            if (raw_dataset === true) {
                document.querySelector('#raw_data_radio1').checked = true;    // Enables raw Dataset
            }
            else {
                document.querySelector('#raw_data_radio2').checked = true;    // Disables raw dataset
            }

            next_frame_enable = daq_config.next_frame.enable;
            if (next_frame_enable === true) {
                document.querySelector('#next_frame_radio1').checked = true;
            }
            else {
                document.querySelector('#next_frame_radio2').checked = true;
            }

            calibration_enable = daq_config.calibration.enable;
            if (calibration_enable === true) {
                document.querySelector('#calibration_radio1').checked = true;
            }
            else {
                document.querySelector('#calibration_radio2').checked = true;
            }
            configure_bin_labels(calibration_enable);

            // const compression = result["detector"]["daq"].compression_type;
            // document.querySelector('#compression-text').value = compression;

            const file_info = result["detector"]["daq"]["file_info"];
            document.querySelector('#hdf-file-path-text').value = file_info.file_dir;
            document.querySelector('#hdf-file-name-text').value = file_info.file_name;

            const summed_image = daq_config.summed_image;
            document.querySelector('#threshold-lower-text').value = summed_image.threshold_lower;
            document.querySelector('#threshold-upper-text').value = summed_image.threshold_upper;
            document.querySelector('#image-frequency-text').value = summed_image.image_frequency;

            const config_path = result["detector"]["fem"].hexitec_config;
            const hexitec_config = config_path.substring(config_path.search("control/"))
            document.querySelector('#hexitec-config-text').value = hexitec_config;

            const elog = result["detector"]["status"].elog;
            document.querySelector('#elog-text').value = elog;
            const dataset_name = daq_config.lvframes.dataset_name;
            document.querySelector('#lv_dataset_select').value = dataset_name;

            const lvframes_frame_frequency = daq_config.lvframes.frame_frequency;
            document.querySelector('#lvframes-frame-frequency-text').value = lvframes_frame_frequency;
            const lvframes_per_second = daq_config.lvframes.per_second;
            document.querySelector('#lvframes-per-second-text').value = lvframes_per_second;

            const lvspectra_frame_frequency = daq_config.lvspectra.frame_frequency;
            document.querySelector('#lvspectra-frame-frequency-text').value = lvspectra_frame_frequency;
            const lvspectra_per_second = daq_config.lvspectra.per_second;
            document.querySelector('#lvspectra-per-second-text').value = lvspectra_per_second;
        })
        .catch(error => {
            console.log("update_ui_with_odin_settings() ERROR: " + error.message);
        });
}

function lvframes_frame_frequency_changed() {
    var frame_frequency = document.querySelector('#lvframes-frame-frequency-text');
    hexitec_endpoint.put(parseInt(frame_frequency.value), 'detector/daq/config/lvframes/frame_frequency')
        .then(result => {
            frame_frequency.classList.remove('alert-danger');
        })
        .catch(error => {
            frame_frequency.setCustomValidity(error.message);
            frame_frequency.reportValidity();
            frame_frequency.classList.add('alert-danger');
        });
};

function lvframes_per_second_changed() {
    var per_second = document.querySelector('#lvframes-per-second-text');
    hexitec_endpoint.put(parseInt(per_second.value), 'detector/daq/config/lvframes/per_second')
        .then(result => {
            per_second.classList.remove('alert-danger');
        })
        .catch(error => {
            per_second.setCustomValidity(error.message);
            per_second.reportValidity();
            per_second.classList.add('alert-danger');
        });
};

function lvspectra_frame_frequency_changed() {
    var frame_frequency = document.querySelector('#lvspectra-frame-frequency-text');
    hexitec_endpoint.put(parseInt(frame_frequency.value), 'detector/daq/config/lvspectra/frame_frequency')
        .then(result => {
            frame_frequency.classList.remove('alert-danger');
        })
        .catch(error => {
            frame_frequency.setCustomValidity(error.message);
            frame_frequency.reportValidity();
            frame_frequency.classList.add('alert-danger');
        });
};

function lvspectra_per_second_changed() {
    var per_second = document.querySelector('#lvspectra-per-second-text');
    hexitec_endpoint.put(parseInt(per_second.value), 'detector/daq/config/lvspectra/per_second')
        .then(result => {
            per_second.classList.remove('alert-danger');
        })
        .catch(error => {
            per_second.setCustomValidity(error.message);
            per_second.reportValidity();
            per_second.classList.add('alert-danger');
        });
};

function showTime() {
    // Returns a timestamp string in the format "YYYYMMDD_HHMMSS"
    var timeNow = new Date();
    var years = timeNow.getUTCFullYear();
    var months = timeNow.getUTCMonth() + 1; // Make January=1, February=2, etc
    var days = timeNow.getUTCDate();
    var hours = timeNow.getHours();
    var minutes = timeNow.getMinutes();
    var seconds = timeNow.getSeconds();
    // Date uses minimal number of digits; January 1 or 01/01 is
    //  represented by 1/1. Force use 2 digits representation:
    days = ((days < 10) ? "0" : "") + days;
    hours = ((hours < 10) ? "0" : "") + hours;
    months = ((months < 10) ? "0" : "") + months;
    minutes = ((minutes < 10) ? "0" : "") + minutes;
    seconds = ((seconds < 10) ? "0" : "") + seconds;

    var timeString = "" + years;
    timeString += months;
    timeString += days;
    timeString += "_" + hours;
    timeString += minutes;
    timeString += seconds;
    return timeString;
}

/**
 * This function displays the log messages that are returned by the backend in the
 * pre-scrollable element and scrolls down to the bottom of it. It stores the
 * timestamp of the last message so that it can tell the backend which messages it
 * needs to get next. All log messages are returned if the last_message_timestamp is
 * empty and this normally happens when the page is reloaded.
 */
function display_log_messages() {
    get_log_messages()
        .then(result => {
            // console.log("result: " + JSON.stringify(result.fem.log_messages, null, 4))
            log_messages = result.fem.log_messages;
            if (!is_empty_object(log_messages)) {
                last_message_timestamp = log_messages[log_messages.length - 1][0];
                // console.log("pre-loop");
                // console.log("log_messages: " + JSON.stringify(log_messages, null, 4));
                // console.log("   " + log_messages[0]);
                // console.log("   " + log_messages[1]);
                pre_scrollable = document.querySelector('#log-messages');
                for (log_message in log_messages) {
                    // console.log("log_messages[log_message][0]: i.e. log_messages['" + log_message + "'][0] : " + log_messages[log_message][0]);
                    // console.log("log_messages[log_message][1]: i.e. log_messages['" + log_message + "'][1] : " + log_messages[log_message][1]);
                    timestamp = log_messages[log_message][0];
                    timestamp = timestamp.substr(0, timestamp.length - 3);
                    pre_scrollable.innerHTML +=
                        `<span style="color:#007bff">${timestamp}</span> ${log_messages[log_message][1]}<br>`;
                    pre_scrollable.scrollTop = pre_scrollable.scrollHeight;
                }
            }
        })
        .catch(error => {
            alert_message = 'A problem occurred while trying to get log messages: ' + error.message;
            display_alert(ALERT_ID['sequencer_info'], alert_message);
        });
}

/**
 * This function gets the log messages from the backend.
 */
function get_log_messages() {
    return hexitec_endpoint.put({ 'last_message_timestamp': last_message_timestamp }, 'detector/fem')
        .then(hexitec_endpoint.get_url(hexitec_url + 'detector/fem/log_messages')
        );
}

/**
 * This function replicates the equivalent jQuery isEmptyObject, returning true if the
 * object passed as an parameter is empty.
 */
function is_empty_object(obj) {
    return Object.keys(obj).length === 0;
}

/**
 * This function displays the alert and the given alert message by removing
 * the d-none class from the div(s).
 */
function display_alert(alert_id, alert_message) {
    let alert_elem = document.querySelector(alert_id);
    alert_elem.innerHTML = alert_message;
    alert_elem.classList.remove('d-none');
}
