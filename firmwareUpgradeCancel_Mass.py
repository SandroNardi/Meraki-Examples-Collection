import os
import meraki


# Full admin api key required to cancel
API_KEY = os.getenv("MK_TEST_API")

# parameters
AUTO_ADD = False
AUTO_CANCEL = False

dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)

# get all arganization
organizations = dashboard.organizations.getOrganizations()

# for each org
for org in organizations:
    # get any scheduled upgrade
    upgrades = dashboard.organizations.getOrganizationFirmwareUpgrades(
        org["id"], total_pages="all", status="Scheduled"
    )
    print(f"\n> Organization: {org['name']}")

    # if no upgrade is scheduled go to next org
    if len(upgrades) == 0:
        print(f">> No upgrades scheduled for Organization {org['name']}")
        continue

    # if not get all the tework in the org
    networks = dashboard.organizations.getOrganizationNetworks(
        org["id"], total_pages="all"
    )

    # for each network get the scheduled upgrades
    for net in networks:
        net_updates = dashboard.networks.getNetworkFirmwareUpgrades(net["id"])

        # dictionary with each product that has an upgrade that can be changed
        products_to_cancel = {}
        # check if at least one can be cancelled
        more_than_zero_to_cancel = False

        print(f"\n>> Parsing: {net['name']}")
        # for all the product
        for k, product in net_updates["products"].items():

            # if no upgrade is scheduled skip
            if product["nextUpgrade"]["time"] == "":
                continue

            # if current version is not an available target version skip
            if product["currentVersion"] not in product["availableVersions"]:
                print(f">>> Can't cancel {k}, destination FW version not available")
                continue

            if not AUTO_ADD:
                print(
                    f">>> {k}, scheduled upgrade {product['nextUpgrade']['time']}, from {product['currentVersion']['shortName']} to from {product['nextUpgrade']['toVersion']['shortName']}"
                )
                cancelThis = input("Do you want add this to the cancel list? (Y/n)")
                if cancelThis != "Y":
                    print(">>>> not cancelled")
                    continue

            # else mark that there is at least 1 upgrade to cancel
            more_than_zero_to_cancel = True

            # add it in to the dictionary with the necessary configuration
            products_to_cancel[k] = {
                "nextUpgrade": {
                    "time": product["nextUpgrade"]["time"],
                    "toVersion": {"id": product["currentVersion"]["id"]},
                },
                "participateInNextBetaRelease": False,
            }

            # console feedback
            print(
                f">>> {k}, scheduled upgrade {product['nextUpgrade']['time']}, from {product['currentVersion']['shortName']} to from {product['nextUpgrade']['toVersion']['shortName']} - Added"
            )

        # if at least one to cancel
        if more_than_zero_to_cancel:
            if not AUTO_CANCEL:
                cancelAll = input(
                    f"\nDo you want cancel all upgrades for network {net['name']} (Y/n)"
                )
                if cancelAll != "Y":
                    print(f">>>> skip {net['name']}")
                    continue
            # try to PUT
            try:
                response = dashboard.networks.updateNetworkFirmwareUpgrades(
                    net["id"],
                    upgradeWindow=net_updates["upgradeWindow"],
                    timezone=net_updates["timezone"],
                    products=products_to_cancel,
                )
                print(">>>> upgrade cancelled")

            except Exception as e:
                print(">>>> unable to cancel")
                print(e)

        else:
            print(f">>> Nothing to cancel for network {net['name']}")
    # check if there are still scheduled upgrades
    upgrades = dashboard.organizations.getOrganizationFirmwareUpgrades(
        org["id"], total_pages="all", status="Scheduled"
    )

    print(f'\n> Total upgrades still scheduled for {org["name"]}: {len(upgrades)}')
