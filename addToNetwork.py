import meraki
import os
import csv

API_KEY = os.getenv("MK_TEST_API")

dashboard = meraki.DashboardAPI(API_KEY,suppress_logging=True)

organization_id = os.getenv("MK_SIDE_ORG")
network_name="Combined net"

id_ = '1234'
name = 'My VLAN'

serials = []

with open('data/serials.csv') as read_obj:
  csv_reader = csv.reader(read_obj) # pass the file object to reader() to get the reader object
  list_of_rows = list(csv_reader) # Pass reader object to list() to get a list of lists

#print(list_of_rows)


for l in list_of_rows:
   serials.append(l[0])

print("Adding this devices", serials, "to", network_name,"network.")


response = dashboard.organizations.getOrganizationNetworks(
    organization_id, total_pages='all'
)
for r in response:
    if r['name'] == network_name:
        response = dashboard.networks.claimNetworkDevices(
            r['id'], serials
        )
        print ("Devices added\nPerforming some initial configuration...")

        response = dashboard.appliance.updateNetworkApplianceVlansSettings(
            r['id'], 
            vlansEnabled=True
        )

        response = dashboard.appliance.createNetworkApplianceVlan(
            r['id'], id_, name, 
            subnet='10.0.0.0/24', 
            applianceIp='10.0.0.1', 
            cidr='10.0.0.0/24'
            )
        print ("Vlan:",name,"id:",id_, "configured successfully!!\n\nFull details below:")


print(response)