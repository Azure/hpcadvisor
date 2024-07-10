import json
import os
import sys

import requests

from hpcadvisor import logger, utils

log = logger.logger

# TODO: Add support for multiple SKUs so a single query is made

def get_price_from_cache(selected_region, selected_sku):
    cache_file = utils.get_price_cache_filename()
    if not os.path.exists(cache_file):
        return None

    cache = json.load(open(cache_file, "r"))
    if selected_region in cache and selected_sku in cache[selected_region]:
        return cache[selected_region][selected_sku]
    return None

def set_price_in_cache(selected_region, selected_sku, price):

    cache_file = utils.get_price_cache_filename()
    if not os.path.exists(cache_file):
        cache = {}
    else:
        cache = json.load(open(cache_file, "r"))

    if selected_region not in cache:
        cache[selected_region] = {}


    cache[selected_region][selected_sku] = price
    json.dump(cache, open(cache_file, "w"))

def get_price(selected_region, selected_sku):

    price = get_price_from_cache(selected_region, selected_sku)

    if price:
        return price

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
                set_price_in_cache(selected_region, selected_sku, sku["retailPrice"])
                return sku["retailPrice"]

        nextPage = json_data["NextPageLink"]
    return None
