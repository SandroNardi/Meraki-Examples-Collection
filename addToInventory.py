# Script that will read from a csv file a listy  of serials and addit to the selcted org



import os
import meraki
from prettytable import PrettyTable
import csv

# API Functions


# API KEY read only permission is enough
API_KEY = os.getenv("MK_TEST_API")


dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)

serials = []

with open('data/serials.csv') as read_obj:
  csv_reader = csv.reader(read_obj) # pass the file object to reader() to get the reader object
  list_of_rows = list(csv_reader) # Pass reader object to list() to get a list of lists

print(list_of_rows)


for l in list_of_rows:
   serials.append(l[0])

print(serials)


organization_id = os.getenv("MK_SIDE_ORG")


response = dashboard.organizations.claimIntoOrganizationInventory(
    organization_id, 
    serials=serials, 
)

print(response)






