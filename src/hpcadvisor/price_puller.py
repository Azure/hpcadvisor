import json
import sys

import requests

from hpcadvisor import logger

log = logger.logger


# TODO: Add support for multiple SKUs so a single query is made
def get_price(selected_region, selected_sku):
    api_url = (
        "https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview"
    )
    query = f"armRegionName eq '{selected_region}' and priceType eq 'Consumption' "
    response = requests.get(api_url, params={"$filter": query})
    json_data = json.loads(response.text)
    if json_data["Items"] == []:
        print(f"No results found for region '{selected_region}'")
        sys.exit(1)

    nextPage = json_data["NextPageLink"]

    while nextPage:
        response = requests.get(nextPage)
        json_data = json.loads(response.text)
        for sku in json_data["Items"]:
            if (
                selected_sku.lower() in sku["armSkuName"].lower()
                and "Spot" not in sku["skuName"]
                and "Low Priority" not in sku["skuName"]
                and "Windows" not in sku["productName"]
            ):
                return sku["retailPrice"]

        nextPage = json_data["NextPageLink"]
    return None
