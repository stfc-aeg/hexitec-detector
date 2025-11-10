"""
EPAC Triggered mode: Work out LUT logic for farm mode configuration.

Christian Angelsen, STFC Detector Systems Software Group
"""

import sys


def epac_triggering_farm_mode_config(self, ip_addresses, macs, ports, frames_per_trigger):
    """Determine Farm Mode configuration, based on Odin instances and frames per trigger.

    Round-robin, N frames (per trigger) to each Odin instance."""
    lut_entries = frames_per_trigger * (len(ip_addresses) // 2)
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
                ip_lut1.append(ip_addresses[current_instance])
                mac_lut1.append(macs[current_instance])
                port_lut1.append(ports[current_instance])
            else:
                ip_lut2.append(ip_addresses[current_instance+1])
                mac_lut2.append(macs[current_instance+1])
                port_lut2.append(ports[current_instance+1])
        else:
            if (index % 2) == 0:  # Even
                ip_lut1.append(ip_addresses[current_instance+1])
                mac_lut1.append(macs[current_instance+1])
                port_lut1.append(ports[current_instance+1])
            else:
                ip_lut2.append(ip_addresses[current_instance])
                mac_lut2.append(macs[current_instance])
                port_lut2.append(ports[current_instance])
        frame_count += 1
        if frame_count == frames_per_trigger:
            frame_count = 0
            current_instance += 2
            offset += 1
        index += 1
    return ip_lut1, ip_lut2, mac_lut1, mac_lut2, port_lut1, port_lut2

def nxct_untriggering_farm_mode_config(self, ip_addresses, macs, ports):
    """Determine NXCT's Farm Mode configuration, untriggered mode.

    Round-robin, one frame to Odin instance."""
    lut_entries = len(ip_addresses)
    print(f" LUT entries: {lut_entries}")
    ip_lut1 = []
    ip_lut2 = []
    mac_lut1 = []
    mac_lut2 = []
    port_lut1 = []
    port_lut2 = []
    index = 0
    while index < lut_entries:
        if (index % 2) == 0:
            ip_lut1.append(ip_addresses[index])
            mac_lut1.append(macs[index])
            port_lut1.append(ports[index])
        else:
            ip_lut2.append(ip_addresses[index])
            mac_lut2.append(macs[index])
            port_lut2.append(ports[index])
        index += 1
    return ip_lut1, ip_lut2, mac_lut1, mac_lut2, port_lut1, port_lut2

def epac_untriggering_farm_mode_config(self, ip_addresses, macs, ports):
    """Determine EPAC's Farm Mode configuration, untriggered mode.

    Round-robin, one frame to Odin instance."""
    lut_entries = len(ip_addresses)
    print(f" LUT entries: {lut_entries}")
    ip_lut1 = []
    ip_lut2 = []
    mac_lut1 = []
    mac_lut2 = []
    port_lut1 = []
    port_lut2 = []
    index = 0
    added_entries = 0
    while index < lut_entries:
        if (added_entries % 2) == 0:
            print(f" {index} Adding to LUT1: IP {ip_addresses[index]}, Port {ports[index]}")
            ip_lut1.append(ip_addresses[index])
            mac_lut1.append(macs[index])
            port_lut1.append(ports[index])
        else:
            print(f" {index} Adding to LUT2: IP {ip_addresses[index]}, Port {ports[index]}")
            ip_lut2.append(ip_addresses[index])
            mac_lut2.append(macs[index])
            port_lut2.append(ports[index])
        index += 2
        added_entries += 1
    return ip_lut1, ip_lut2, mac_lut1, mac_lut2, port_lut1, port_lut2


if __name__ == '__main__':
    '''
    9c:69:b4:60:b8:25 - 10.0.1.1    9c:69:b4:60:b8:26 - 10.0.2.1
    '''
    try:
        choice = int(sys.argv[1])
        odin_pairs = int(sys.argv[2])
        if odin_pairs == 2:
            addresses = ['10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1']
            ports = [61650, 61650, 61651, 61651]
            macs = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26']
        elif odin_pairs == 4:
            addresses = ['10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1', '10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1']
            macs = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26',
                    '9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26']
            ports = ['61650', '61650', '61651', '61651', '61652', '61652', '61653', '61653']
        elif odin_pairs == 6:
            # Develop round-robin, 1 frame for each Odin pair
            print("untriggered, 2 Odin pairs.")
            addresses = ['10.0.2.1', '10.0.1.1']
            ports = [61649, 61649]
            macs = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25']
        elif odin_pairs == 8:
            # Develop round-robin, 1 frame for each Odin pair
            print("untriggered, 4 Odin pairs.")
            addresses = ['10.0.2.1', '10.0.1.1', '10.0.2.1', '10.0.1.1']
            macs = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25',
                    '9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25']
            ports = ['61650', '61650', '61651', '61651']
        elif odin_pairs == 10:
            # EPAC -- Untriggered Farm Mode Config
            # FM; frames_per_trigger = 2
            addresses = ['10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1']
            ports = [61650, 61650, 61651, 61651]
            macs = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26']
            # FM; DL0: 10.0.2.1, 9c:69:b4:60:b8:26
            # FM; DL1: 10.0.1.1, 9c:69:b4:60:b8:25
            # FM; ips1: ['10.0.2.1', '10.0.1.1'] ips2: ['10.0.1.1', '10.0.2.1']
            # FM; macs1: ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25'] macs2: ['9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26']
            # FM; ports1: [61650, 61651] ports2: [61650, 61651]
            #  LUT entries: 2 for 4 targets
        elif odin_pairs == 12:
            #  -- Untriggered Farm Mode Config
            # FM; frames_per_trigger = 2
            addresses = ['10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1', '10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1']
            ports = [61650, 61650, 61651, 61651, 61652, 61652, 61653, 61653]
            macs = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26', '9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26']
        else:
            print("Invalid number of Odin pairs. Use 2 or 4.")
            sys.exit(1)
        frames_per_trigger = int(sys.argv[3])
        if choice == 0:
            print(epac_triggering_farm_mode_config("", addresses, macs, ports, frames_per_trigger))
        elif choice == 1:
            print(nxct_untriggering_farm_mode_config("", addresses, macs, ports))
        elif choice == 2:
            print(epac_untriggering_farm_mode_config("", addresses, macs, ports))
        else:
            print("Invalid choice. Use 0 for even frames or 1 for odd frames.")
    except IndexError:
        print("Usage:")
        print("farm_mode_configurator.py <0 or 1> <2 or 4> <frames_per_trigger>")
        print("such as:")
        print("farm_mode_configurator.py 0 2 6 # for 2 Odin pairs and 6 frames/trigger")
        print("or")
        print("farm_mode_configurator.py 1 4 5 # for 4 Odin pairs and 5 frames/trigger")


