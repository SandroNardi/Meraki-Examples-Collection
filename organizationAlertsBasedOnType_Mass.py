import os
import meraki
from prettytable import PrettyTable
from datetime import datetime, timedelta
import pytz

# API KEY read only permission is enough
API_KEY = os.getenv("MK_TEST_API")

# Org alert pram
# from https://developer.cisco.com/meraki/api-v1/get-organization-assurance-alerts/ deviceTypes supported : MX - MS - MR - Z - VMX - Catalyst Switch - Catalyst AP
alerts_type_of_devices = ["MR", "MX", "MV"]
# from https://developer.cisco.com/meraki/api-v1/get-organization-assurance-alerts/ types - match "Category" column in the table, empty list for all type of alerts
alerts_type_of_alerts = ["unreachable", "bad_connectivity"]
# alerst starded and resolved delta days
orgAlertDaysDeltaTimes = 5

# output tables headers
t_resolved = PrettyTable(
    ["D-Type", "Alert type", "Name", "Serial", "Started", "Stopped"]
)
t_active = PrettyTable(["D-Type", "Alert type", "Name", "Serial", "Started"])


dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)

organizations = dashboard.organizations.getOrganizations()

# time zone and time frame calculations
# Set the timezone to UTC (which is equivalent to GMT for our purposes)
utc_timezone = pytz.timezone("UTC")
# Get the current date and time in UTC
current_date_utc = datetime.now(utc_timezone)
# Subtract 30 days from the current date
date_deltaTime_days_ago = current_date_utc - timedelta(days=orgAlertDaysDeltaTimes)
# Format the date as a string in ISO 8601 format with 'Z' for Zulu/UTC time
date_string = date_deltaTime_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ")


for org in organizations:
    t_resolved.clear_rows()
    t_active.clear_rows()

    alerts = dashboard.organizations.getOrganizationAssuranceAlerts(
        org["id"],
        total_pages="all",
        active=True,
        resolved=True,
        tsStart=date_string,
    )

    for alert in alerts:
        if alert["deviceType"] not in alerts_type_of_devices:
            continue
        if alert["type"] not in alerts_type_of_alerts:
            continue

        for device in alert["scope"]["devices"]:

            if alert["resolvedAt"] == None:
                t_active.add_row(
                    [
                        alert["deviceType"],
                        alert["type"],
                        device["name"],
                        device["serial"],
                        alert["startedAt"],
                    ]
                )
            else:
                t_resolved.add_row(
                    [
                        alert["deviceType"],
                        alert["type"],
                        device["name"],
                        device["serial"],
                        alert["startedAt"],
                        alert["resolvedAt"],
                    ]
                )

    print(f"\n{org['name']}")
    print(f"Active alerts")
    print(t_active)
    print(f"Resolved alerts")
    print(t_resolved)
