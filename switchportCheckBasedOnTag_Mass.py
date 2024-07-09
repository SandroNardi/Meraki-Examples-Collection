import os
import meraki

# API call to get Switchport current config https://developer.cisco.com/meraki/api-v1/get-device-switch-ports/
# API call to get Switchport current status https://developer.cisco.com/meraki/api-v1/get-device-switch-ports-statuses/

# search for all org, all switchport and based on tag identify ports down, disconnected, with error, with warnings and 100 mbps links

# switchport tag
switchportTag = "VIP"


# API KEY read only permission is enough
API_KEY = os.getenv("MK_TEST_API")


dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)

# tag name port up duplex speed

organizations = dashboard.organizations.getOrganizations()
# for each org get the devices and the devices status
for org in organizations:
    # gat all switches
    switches = dashboard.organizations.getOrganizationDevices(
        org["id"], total_pages="all", productTypes=["switch"]
    )
    for switch in switches:

        switchportConfig = dashboard.switch.getDeviceSwitchPorts(switch["serial"])
        switchportStatus = dashboard.switch.getDeviceSwitchPortsStatuses(
            switch["serial"]
        )

        for swPortConf in switchportConfig:

            if switchportTag not in swPortConf["tags"]:
                continue

            for swPortStat in switchportStatus:

                if swPortStat["portId"] != swPortConf["portId"]:
                    continue

                switchStr = switch["name"] + " - Port: " + swPortStat["portId"]

                # port disabled
                if swPortStat["enabled"] == False:
                    print(f"= {switchStr} - Admin Disabled")
                    continue
                # port disconnected
                if swPortStat["status"] == "Disconnected":
                    print(f"= {switchStr} - Disconnected")
                    continue
                # port connected with errors
                if (
                    len(swPortStat["errors"]) > 0
                    and swPortStat["status"] == "Connected"
                ):
                    print(f"= {switchStr} - UP with errors : {swPortStat['errors']}")
                    continue

                # port connected with warnings
                if (
                    len(swPortStat["warnings"]) > 0
                    and swPortStat["status"] == "Connected"
                ):
                    print(
                        f"= {switchStr} - UP with warnings : {swPortStat['warnings']}"
                    )
                    continue
                # 100 mbps unexpected
                if (
                    swPortConf["linkNegotiation"] != "100 Megabit (auto)"
                    and swPortStat["speed"] == "100 Mbps"
                ):
                    print(f"= {switchStr} - Unexpected 100 mbps")
