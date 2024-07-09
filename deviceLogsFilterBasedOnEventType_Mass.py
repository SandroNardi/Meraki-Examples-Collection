# Script that for each network will fetch event log of a specific product type and specific events sorted descending by timestamp

# This is a Mass script it will execute on all organizations accessible with the provided API key

import os
import meraki
from prettytable import PrettyTable

# API Functions
# https://developer.cisco.com/meraki/api-v1/get-organizations/
# https://developer.cisco.com/meraki/api-v1/get-organization-networks/
# https://developer.cisco.com/meraki/api-v1/get-network-events/


# prduct type, must match productType query param in documentation
productType = "switch"

# List of event to filter for. Matches the "Category" column. Empty list for all
includedEventTypes = ["boot", "radius_mac_auth"]


# API KEY read only permission is enough
API_KEY = os.getenv("MK_TEST_API")

total_pages = 10

dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)
organizations = dashboard.organizations.getOrganizations()

for org in organizations:
    # get all network
    networks = dashboard.organizations.getOrganizationNetworks(
        org["id"], total_pages="all"
    )

    # for each network if it contains a switch
    for net in networks:
        # eventTypes = dashboard.networks.getNetworkEventsEventTypes(net["id"])
        # print(eventTypes)

        if productType in net["productTypes"]:
            # get network events for the switches in the "boot" category
            events = dashboard.networks.getNetworkEvents(
                net["id"],
                total_pages=total_pages,
                productType=productType,
                includedEventTypes=includedEventTypes,
            )
            # put in table
            t_devices = PrettyTable(
                ["Time", "Name", "Serial", "Description", "Category", "Reason"]
            )
            for event in events["events"]:

                t_devices.add_row(
                    [
                        event["occurredAt"],
                        event["deviceName"],
                        event["deviceSerial"],
                        event["description"],
                        event["category"],
                        event["eventData"],
                    ]
                )
            # print table
            print(t_devices)
