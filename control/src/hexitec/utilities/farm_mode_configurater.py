"""
EPAC Triggered mode: Work out LUT logic for farm mode configuration.

Christian Angelsen, STFC Detector Systems Software Group
"""

import sys


def determine_farm_mode_config_odd_frames(self, odin_instances, macs, ports, frames_per_trigger):
    """Determine Farm Mode configuration, based on Odin instances and frames per trigger"""
    print(f"Selected ODD frames configuration; {len(odin_instances)//2} Odin pair(s), {frames_per_trigger} frames/trigger")
    lut_entries = frames_per_trigger * (len(odin_instances) // 2)
    ip_lut1 = []
    ip_lut2 = []
    mac_lut1 = []
    mac_lut2 = []
    port_lut1 = []
    port_lut2 = []
    frame_count = 0
    current_instance = 0
    index = 0
    offset = 0
    while index < lut_entries:
        if (offset % 2) == 0:
            if (index % 2) == 0:  # Even
                print(f"{offset}:{index}: (c_i: {current_instance}) Adding {odin_instances[current_instance]} to ip_lut1")
                ip_lut1.append(odin_instances[current_instance])
                mac_lut1.append(macs[current_instance])
                port_lut1.append(ports[current_instance])
            else:
                print(f"{offset}:{index}: (c_i: {current_instance+1}) Adding {odin_instances[current_instance+1]} to ip_lut2")
                ip_lut2.append(odin_instances[current_instance+1])
                mac_lut2.append(macs[current_instance+1])
                port_lut2.append(ports[current_instance+1])
        else:
            if (index % 2) == 0:  # Even
                print(f"{offset}:{index}: (c_i: {current_instance+1}) Adding {odin_instances[current_instance+1]} to ip_lut1")
                ip_lut1.append(odin_instances[current_instance+1])
                mac_lut1.append(macs[current_instance+1])
                port_lut1.append(ports[current_instance+1])
            else:
                print(f"{offset}:{index}: (c_i: {current_instance}) Adding {odin_instances[current_instance]} to ip_lut2")
                ip_lut2.append(odin_instances[current_instance])
                mac_lut2.append(macs[current_instance])
                port_lut2.append(ports[current_instance])
        frame_count += 1
        if frame_count == frames_per_trigger:
            print(f"Frame count reached {frames_per_trigger}, c_i becomes: {current_instance + 2}")
            frame_count = 0
            current_instance += 2
            offset += 1
        index += 1
    return ip_lut1, ip_lut2, mac_lut1, mac_lut2, port_lut1, port_lut2

def determine_farm_mode_config_even_frames(self, odin_instances, macs, ports, frames_per_trigger):
    """Determine Farm Mode configuration, based on Odin instances and frames per trigger"""
    print(f"Selected EVEN frames configuration; {len(odin_instances)//2} Odin pair(s), {frames_per_trigger} frames/trigger")
    lut_entries = frames_per_trigger * (len(odin_instances) // 2)
    ip_lut1 = []
    ip_lut2 = []
    mac_lut1 = []
    mac_lut2 = []
    port_lut1 = []
    port_lut2 = []
    frame_count = 0
    current_instance = 0
    index = 0
    offset = 0
    while index < lut_entries:
        if (index % 2) == 0:  # Even
            print(f"{offset}:{index}: (c_i: {current_instance}) Adding {odin_instances[current_instance]} to ip_lut1")
            ip_lut1.append(odin_instances[current_instance])
            mac_lut1.append(macs[current_instance])
            port_lut1.append(ports[current_instance])
        else:
            print(f"{offset}:{index}: (c_i: {current_instance}) Adding {odin_instances[current_instance]} to ip_lut2")
            ip_lut2.append(odin_instances[current_instance])
            mac_lut2.append(macs[current_instance])
            port_lut2.append(ports[current_instance])
        frame_count += 1
        if frame_count == frames_per_trigger:
            print(f"Frame count reached {frames_per_trigger}, c_i becomes: {current_instance + 2}")
            frame_count = 0
            current_instance += 2
            # offset += 1
        index += 1
    return ip_lut1, ip_lut2, mac_lut1, mac_lut2, port_lut1, port_lut2


if __name__ == '__main__':
    '''
    9c:69:b4:60:b8:25 - 10.0.1.1
    9c:69:b4:60:b8:26 - 10.0.2.1
    '''
    try:
        choice = int(sys.argv[1])
        odin_pairs = int(sys.argv[2])
        if odin_pairs == 2:
            odin_instances = ['10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1']
            macs = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26']
            ports = ['61649', '61659', '61649', '61659']
        elif odin_pairs == 4:
            odin_instances = ['10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1', '10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1']
            macs = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26',
                    '9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26']
            ports = ['61649', '61659', '61649', '61659', '61669', '61679', '61669', '61679']
        else:
            print("Invalid number of Odin pairs. Use 2 or 4.")
            sys.exit(1)
        frames_per_trigger = int(sys.argv[3])
        if choice == 0:
            print (determine_farm_mode_config_even_frames("", odin_instances, macs, ports, frames_per_trigger))
        elif choice == 1:
            print (determine_farm_mode_config_odd_frames("", odin_instances, macs, ports, frames_per_trigger))
        else:
            print("Invalid choice. Use 0 for even frames or 1 for odd frames.")
    except IndexError:
        print("Usage:")
        print("farm_mode_configurator.py <0 or 1> <2 or 4> <frames_per_trigger>")
        print("such as:")
        print("farm_mode_configurator.py 0 2 6 # for 2 Odin pairs and 6 frames/trigger")
        print("or")
        print("farm_mode_configurator.py 1 4 5 # for 4 Odin pairs and 5 frames/trigger")
