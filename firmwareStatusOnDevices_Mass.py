import os
import meraki
from prettytable import PrettyTable
import terminalColors as c

# API KEY read only permission is enough
API_KEY = os.getenv("MK_TEST_API")


# default table and matrix cells

table_cell_devices = {
    "on": c.colors["green"] + "YES" + c.colors["stop"],
    "off": c.colors["red"] + "NO" + c.colors["stop"],
    "mismatch": c.colors["yellow"] + "MIS" + c.colors["stop"],
    "lock": c.colors["blue"] + "LOCK" + c.colors["stop"],
    "ok": c.colors["green"] + "OK" + c.colors["stop"],
}
table_cell_summary = {
    "online": c.colors["green"] + "Online" + c.colors["stop"],
    "offline": c.colors["red"] + "Offline" + c.colors["stop"],
    "match": c.colors["green"] + "Match" + c.colors["stop"],
    "mismatch": c.colors["yellow"] + "Mismatch" + c.colors["stop"],
    "locked": c.colors["blue"] + "Locked" + c.colors["stop"],
    "totals": c.colors["white"] + "Totals" + c.colors["stop"],
}


dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


organizations = dashboard.organizations.getOrganizations()
# for each org get the devices and the devices status
for org in organizations:
    print(
        f"\n\n{c.colors['white']}=== {org['name']} / {org['id']} ==={c.colors['stop']}"
    )

    # get devices
    devices = dashboard.organizations.getOrganizationDevices(
        org["id"], total_pages="all"
    )
    # get devices status
    devices_status = dashboard.organizations.getOrganizationDevicesStatuses(
        org["id"], total_pages="all"
    )

    # counters
    on_mismatch_qty = 0
    on_locked_qty = 0
    on_ok_qty = 0
    off_mismatch_qty = 0
    off_locked_qty = 0
    off_ok_qty = 0

    t_devices = PrettyTable(["Online", "FW Status", "Name", "Serial"])

    # for each device
    for device in devices:
        # find the status
        status_list = [d for d in devices_status if d["serial"] == device["serial"]]

        # 3 cases
        # "Not running configured version" firmware mismatch
        # "Firmware locked. Please contact support" firmware locked
        # <the FW version> all good
        # for each case also split online and offline devices
        if device["firmware"] == "Not running configured version":
            if status_list[0]["status"] == "online":
                t_devices.add_row(
                    [
                        table_cell_devices["on"],
                        table_cell_devices["mismatch"],
                        device["name"],
                        device["serial"],
                    ]
                )
                on_mismatch_qty += 1
                continue
            else:
                t_devices.add_row(
                    [
                        table_cell_devices["off"],
                        table_cell_devices["mismatch"],
                        device["name"],
                        device["serial"],
                    ]
                )
                off_mismatch_qty += 1
                continue

        if device["firmware"] == "Firmware locked. Please contact support":
            if status_list[0]["status"] == "online":
                t_devices.add_row(
                    [
                        table_cell_devices["on"],
                        table_cell_devices["lock"],
                        device["name"],
                        device["serial"],
                    ]
                )
                on_locked_qty += 1
                continue
            else:
                t_devices.add_row(
                    [
                        table_cell_devices["off"],
                        table_cell_devices["lock"],
                        device["name"],
                        device["serial"],
                    ]
                )
                off_locked_qty += 1
                continue

        if status_list[0]["status"] == "online":
            t_devices.add_row(
                [
                    table_cell_devices["on"],
                    table_cell_devices["ok"],
                    device["name"],
                    device["serial"],
                ]
            )
            on_ok_qty += 1

        else:
            t_devices.add_row(
                [
                    table_cell_devices["off"],
                    table_cell_devices["ok"],
                    device["name"],
                    device["serial"],
                ]
            )
            off_ok_qty += 1

    print(t_devices)

    # online devices
    status_list = [d for d in devices_status if d["status"] == "online"]

    # create and print summary for the org
    print(
        f"\n> SUMMARY for {org['name']} / {org['id']}\n> Devices online {len(status_list)}/{len(devices)}"
    )

    t_summary = PrettyTable(
        [
            "Status",
            table_cell_summary["match"],
            table_cell_summary["mismatch"],
            table_cell_summary["locked"],
            table_cell_summary["totals"],
        ]
    )
    t_summary.add_row(
        [
            table_cell_summary["online"],
            on_ok_qty,
            on_mismatch_qty,
            on_locked_qty,
            on_ok_qty + on_mismatch_qty + on_locked_qty,
        ]
    )
    t_summary.add_row(
        [
            table_cell_summary["offline"],
            off_ok_qty,
            off_mismatch_qty,
            off_locked_qty,
            off_ok_qty + off_mismatch_qty + off_locked_qty,
        ]
    )
    t_summary.add_row(
        [
            table_cell_summary["totals"],
            on_ok_qty + off_ok_qty,
            on_mismatch_qty + off_mismatch_qty,
            on_locked_qty + off_locked_qty,
            len(devices),
        ]
    )

    print(t_summary)
