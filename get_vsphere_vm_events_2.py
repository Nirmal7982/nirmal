
#!/usr/bin/env python

import argparse
import atexit
import ssl
import csv
import os
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from datetime import datetime, timedelta

def get_vm_events(service_instance, start_time, event_types):
    event_manager = service_instance.content.eventManager
    event_filter_spec = vim.event.EventFilterSpec()
    event_filter_spec.time = vim.event.EventFilterSpec.ByTime()
    event_filter_spec.time.beginTime = start_time
    event_filter_spec.eventTypeId = event_types
    events = event_manager.QueryEvents(event_filter_spec)
    return events

def get_cluster_name(vm):
    try:
        if vm and hasattr(vm, 'runtime') and vm.runtime.host and vm.runtime.host.parent:
            return vm.runtime.host.parent.name
    except AttributeError:
        pass
    return "Unknown Cluster"

def append_to_csv(events, csv_file, vcenter_ip):
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write header only if the file doesn't exist
        if not file_exists:
            writer.writerow(['Event', 'Time', 'Vcenter IP', 'Cluster', 'User'])

        for event in events:
            cluster_name = get_cluster_name(event.vm) if hasattr(event, 'vm') else "N/A"
            user = getattr(event, 'userName', 'N/A')
            writer.writerow([event.fullFormattedMessage, event.createdTime, vcenter_ip, cluster_name, user])

def main():
    parser = argparse.ArgumentParser(description="Fetch VM events from vSphere")
    parser.add_argument("--vcenter_ip", required=True, help="vCenter Server IP address")
    parser.add_argument("--username", required=True, help="vCenter Username")
    parser.add_argument("--password", required=True, help="vCenter Password")
    parser.add_argument("--csv_file", required=True, help="CSV file to save the events")

    args = parser.parse_args()
    vcenter_ip = args.vcenter_ip

    # SSL context for unverified certificates
    context = ssl._create_unverified_context()
    service_instance = SmartConnect(host=vcenter_ip, user=args.username, pwd=args.password, sslContext=context)
    atexit.register(Disconnect, service_instance)

    # Set start_time to 1 hour before the current time
    start_time = datetime.now() - timedelta(hours=1)
    event_types = ['VmCreatedEvent', 'VmRemovedEvent', 'VmRenamedEvent']

    events = get_vm_events(service_instance, start_time, event_types)
    append_to_csv(events, args.csv_file, vcenter_ip)

if __name__ == "__main__":
    main()
