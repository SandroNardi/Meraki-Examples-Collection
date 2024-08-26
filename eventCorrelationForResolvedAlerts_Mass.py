import meraki
from prettytable import PrettyTable
from datetime import datetime, timedelta
import pytz
import os
import terminalColors as c


# empty cell in table
FS = "---"
# max lenght of table "info" column
MAX_LEN = 40

# API KEY read only
API_KEY = os.getenv("MK_TEST_API")


# Org alert pram
# from https://developer.cisco.com/meraki/api-v1/get-organization-assurance-alerts/ deviceTypes supported : MX - MS - MR - Z - VMX - Catalyst Switch - Catalyst AP
alerts_type_of_devices = ["MS"]
# from https://developer.cisco.com/meraki/api-v1/get-organization-assurance-alerts/ types - match "Category" column in the table, empty list for all type of alerts
alerts_type_of_alerts = []
# alerst starded and resolved delta days
orgAlertDaysDeltaTimes = 2

# event log param
# event log to exclude, match "Category" column
log_excluded_event_types = []

# events to collect and display
inTable = {"changeLog": True, "eventLog": True, "orgAlert": True, "deviceStatus": True}

# events to collect delta times minutes
delta_times_minutes = {
    "changelogStart": 10,
    "changelogStop": 10,
    "deviceLogStart": 5,
    "deviceLogStop": 5,
    "deviceStatusNext": 5,
}


# ==================

log_device_type_mapping = {
    "Z": "appliance",
    "MX": "appliance",
    "VMX": "appliance",
    "MS": "switch",
    "Catalyst Switch": "switch",
    "Catalyst AP": "wireless",
    "MR": "wireless",
}

event_names = {
    "change": "Change Log",
    "event": "Event Log",
    "orgAlert": "Org Alert",
    "status": "Device status",
}


# output tables headers
t_history = PrettyTable(
    [
        "Time ( UTC )",
        "Source",
        "Dev/Cli/Admin",
        "Category",
        "Description",
        "Info",
    ]
)

dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)
organizations = dashboard.organizations.getOrganizations()


print(
    f"Events triggered and resolved in the last {orgAlertDaysDeltaTimes} days on this device types {alerts_type_of_devices}. # of excluded alert types: {len(alerts_type_of_alerts)}"
)

print(f"Looking for: {inTable}")
print(
    f"Admin ChangeLog range from {delta_times_minutes['changelogStart']} min before event start to {delta_times_minutes['changelogStart']} min after event resolved"
)
print(
    f"Device EventLog range from {delta_times_minutes['deviceLogStart']} min before event start to {delta_times_minutes['deviceLogStop']} min after event resolved. # of exclude events categories: {len(log_excluded_event_types)}"
)
print(
    f"Device status change monitored from event start to {delta_times_minutes['deviceStatusNext']} min after event resolved"
)

input("Press ENTER to continue...")


# time window calculations
alert_tsStart = (
    datetime.now(pytz.timezone("UTC")) - timedelta(days=orgAlertDaysDeltaTimes)
).strftime("%Y-%m-%dT%H:%M:%SZ")

for org in organizations:

    # Construct the base arguments for the function call
    function_args = {
        "total_pages": "all",
        "resolved": True,
        "active": False,
        "tsStart": alert_tsStart,
    }

    # Check if alerts_type_of_alerts is not an empty list and add it to the arguments
    if len(alerts_type_of_alerts) != 0:
        function_args["types"] = alerts_type_of_alerts

    # Call the function with the constructed arguments
    alerts = dashboard.organizations.getOrganizationAssuranceAlerts(
        org["id"], **function_args
    )

    for alert in alerts:
        if alert["deviceType"] not in alerts_type_of_devices:
            continue
            # if alert["type"] not in alerts_type_of_alerts:
            continue

        for device in alert["scope"]["devices"]:
            t_history.clear_rows()
            dt_eventStart = datetime.strptime(alert["startedAt"], "%Y-%m-%dT%H:%M:%SZ")
            dt_eventResolved = datetime.strptime(
                alert["resolvedAt"], "%Y-%m-%dT%H:%M:%SZ"
            )

            print(
                f'\n{c.colors["white"]}{alert["deviceType"]} - {device["name"]} - {device["serial"]} {c.colors["stop"]}'
            )
            print(f' Alert detected : {alert["type"]}')
            print(
                f' Started {dt_eventStart.strftime("%Y-%m-%d")} at {dt_eventStart.strftime("%H:%M:%S")} {dt_eventStart.replace(tzinfo=pytz.utc).tzname()}'
            )
            print(
                f' Stopped {dt_eventResolved.strftime("%Y-%m-%d")} at {dt_eventResolved.strftime("%H:%M:%S")} {dt_eventResolved.replace(tzinfo=pytz.utc).tzname()}'
            )
            print(f" Total duration: {dt_eventResolved-dt_eventStart} ")

            if inTable["orgAlert"]:
                t_history.add_row(
                    [
                        dt_eventStart.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        c.colors["red"] + event_names["orgAlert"] + c.colors["stop"],
                        c.colors["red"] + device["name"] + c.colors["stop"],
                        c.colors["red"] + alert["type"] + c.colors["stop"],
                        c.colors["red"] + ">>> STARTED" + c.colors["stop"],
                        FS,
                    ]
                )
                t_history.add_row(
                    [
                        dt_eventResolved.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        c.colors["green"] + event_names["orgAlert"] + c.colors["stop"],
                        c.colors["green"] + device["name"] + c.colors["stop"],
                        c.colors["green"] + alert["type"] + c.colors["stop"],
                        c.colors["green"] + "<<< STOPPED" + c.colors["stop"],
                        FS,
                    ]
                )

            # get device statatus change in time frame
            if inTable["deviceStatus"]:
                logAfterString = (
                    dt_eventResolved
                    + timedelta(minutes=delta_times_minutes["deviceLogStop"])
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
                statusChanges = dashboard.organizations.getOrganizationDevicesAvailabilitiesChangeHistory(
                    org["id"],
                    total_pages="all",
                    t0=alert["startedAt"],
                    t1=logAfterString,
                    serials=device["serial"],
                )

                for stat in statusChanges:

                    if len(stat["details"]["new"]) == 2:

                        t_history.add_row(
                            [
                                stat["ts"],
                                event_names["status"],
                                stat["device"]["name"],
                                stat["details"]["new"][0]["value"],
                                stat["details"]["new"][1]["value"],
                                FS,
                            ]
                        )

                    else:
                        t_history.add_row(
                            [
                                stat["ts"],
                                event_names["status"],
                                stat["device"]["name"],
                                stat["details"]["new"][0]["value"],
                                FS,
                                FS,
                            ]
                        )

            # get admin change in network in last x h before start
            if inTable["changeLog"]:
                changeT0 = (
                    dt_eventStart
                    - timedelta(minutes=delta_times_minutes["changelogStart"])
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

                changeT1 = (
                    dt_eventStart
                    + timedelta(minutes=delta_times_minutes["changelogStop"])
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

                changes = dashboard.organizations.getOrganizationConfigurationChanges(
                    org["id"],
                    total_pages=3,
                    networkId=alert["network"]["id"],
                    t0=changeT0,
                    t1=changeT1,
                )

                for change in changes:
                    t_history.add_row(
                        [
                            change["ts"],
                            event_names["change"],
                            change["adminName"],
                            change["page"],
                            change["label"],
                            str(change["newValue"])[:MAX_LEN],
                        ]
                    )
            # get device logs in the time frame
            if inTable["eventLog"]:

                logDeltaBeforeStr = (
                    dt_eventStart
                    - timedelta(minutes=delta_times_minutes["deviceLogStart"])
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

                logDeltaAfterStr = (
                    dt_eventResolved
                    + timedelta(minutes=delta_times_minutes["deviceLogStop"])
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

                # print("event log start  ", logDeltaBeforeStr, " stop", logDeltaAfterStr)
                events = dashboard.networks.getNetworkEvents(
                    alert["network"]["id"],
                    perPage=500,
                    deviceSerial=device["serial"],
                    productType=log_device_type_mapping[alert["deviceType"]],
                    excludedEventTypes=log_excluded_event_types,
                    # startingAfter=logDeltaAfterStr,
                )

                # print(len(events["events"]))
                # print(events["events"][-1]["occurredAt"])
                # print(events["events"][0]["occurredAt"])
                for event in events["events"]:
                    if datetime.strptime(
                        event["occurredAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    ) < datetime.strptime(logDeltaBeforeStr, "%Y-%m-%dT%H:%M:%SZ"):
                        break

                    if datetime.strptime(
                        event["occurredAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    ) > datetime.strptime(logDeltaAfterStr, "%Y-%m-%dT%H:%M:%SZ"):
                        continue

                    client = "-"
                    if (
                        event["deviceName"] != "None"
                        and event["deviceName"] != None
                        and event["deviceName"] != ""
                    ):
                        client = event["deviceName"]
                    if (
                        event["clientMac"] != "None"
                        and event["clientMac"] != None
                        and event["clientMac"] != ""
                    ):
                        client = event["clientMac"]

                    if (
                        event["clientDescription"] != "None"
                        and event["clientDescription"] != None
                        and event["clientDescription"] != ""
                    ):
                        client = event["clientDescription"]

                    t_history.add_row(
                        [
                            event["occurredAt"],
                            event_names["event"],
                            client,
                            event["category"],
                            event["description"],
                            str(event["eventData"])[:MAX_LEN],
                        ]
                    )

            # print table
            print(t_history.get_string(sortby="Time ( UTC )"))
