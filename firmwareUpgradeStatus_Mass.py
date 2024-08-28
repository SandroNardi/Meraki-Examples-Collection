import os
import meraki


# Read only enough
API_KEY = os.getenv("MK_TEST_API")


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

            more_than_zero_to_cancel = True
            print(
                f">>> {k}, scheduled upgrade {product['nextUpgrade']['time']}, from {product['currentVersion']['shortName']} to from {product['nextUpgrade']['toVersion']['shortName']}"
            )
        if not more_than_zero_to_cancel:
            print(">>> no upgrade to cancel for this network")
    # check if there are still scheduled upgrades
    upgrades = dashboard.organizations.getOrganizationFirmwareUpgrades(
        org["id"], total_pages="all", status="Scheduled"
    )

    print(f'\n> Total upgrades scheduled for {org["name"]}: {len(upgrades)}')
