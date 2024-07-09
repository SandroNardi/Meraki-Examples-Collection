# Script that fetch all the devices stataus changes an dispaly them divided by devices sorted descending by timestamp

# This is a Mass script it will execute on all organizations accessible with the provided API key

import meraki
from prettytable import PrettyTable
import os

# API Functions
# https://developer.cisco.com/meraki/api-v1/get-organizations/
# https://developer.cisco.com/meraki/api-v1/get-organization-devices/
# https://developer.cisco.com/meraki/api-v1/get-organization-devices-availabilities-change-history/


# place holder for an empty cell in table
FS = "---"

# API KEY read only permission
API_KEY = os.getenv("MK_TEST_API")

# Device availability timespan. The value must be in seconds and be less than or equal to 31 days. The default is 1 day. Maximum = 2678400
timespan = 2678400

# output table headers
t_history = PrettyTable(
    [
        "Time ( UTC )",
        "Model",
        "Device name",
        "Category",
        "Description",
    ]
)


dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)
organizations = dashboard.organizations.getOrganizations()

for org in organizations:

    devices = dashboard.organizations.getOrganizationDevices(
        org["id"], total_pages="all"
    )

    serials = [i["serial"] for i in devices]

    # get all stataus changes in timeframe
    statusChanges = (
        dashboard.organizations.getOrganizationDevicesAvailabilitiesChangeHistory(
            org["id"], total_pages="all", serials=serials, timespan=timespan
        )
    )

    # if no results go to next org
    if len(statusChanges) == 0:
        continue

    # sort the list based on serial number
    sorted_list = sorted(statusChanges, key=lambda x: x["device"]["serial"])

    # print separate tables based on the device serial number sorted by time

    # store the first serial number of the list
    sn = sorted_list[0]["device"]["serial"]
    for stat in sorted_list:
        # if the current serial numebr is different form the previous, print the table so far, and clear all rows
        if sn != stat["device"]["serial"]:
            print(t_history.get_string(sortby="Time ( UTC )"))
            t_history.clear_rows()

        # update current serial number
        sn = stat["device"]["serial"]

        # add rows to the table
        if len(stat["details"]["new"]) == 2:

            t_history.add_row(
                [
                    stat["ts"],
                    stat["device"]["model"],
                    stat["device"]["name"],
                    stat["details"]["new"][0]["value"],
                    stat["details"]["new"][1]["value"],
                ]
            )
        if len(stat["details"]["new"]) > 2:

            t_history.add_row(
                [
                    stat["ts"],
                    stat["device"]["model"],
                    stat["device"]["name"],
                    stat["details"]["new"][0]["value"],
                    "3 OR MORE ADDITIONAL VALUES IN RESPONSE",
                ]
            )
        else:
            t_history.add_row(
                [
                    stat["ts"],
                    stat["device"]["model"],
                    stat["device"]["name"],
                    stat["details"]["new"][0]["value"],
                    FS,
                ]
            )
    # print last table
    print(t_history.get_string(sortby="Time ( UTC )"))
