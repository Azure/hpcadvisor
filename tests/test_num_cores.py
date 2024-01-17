import os
import sys

import pytest

from hpcadvisor import batch_handler


def test_get_total_cores():
    SUBSCRIPTION = os.environ.get("SUBSCRIPTION")
    REGION = os.environ.get("REGION")
    assert SUBSCRIPTION is not None
    assert REGION is not None

    batch_handler.env["SUBSCRIPTION"] = batch_handler.get_subscription_id(SUBSCRIPTION)

    batch_handler.env["REGION"] = REGION

    sku = "Standard_D2s_v3"
    cores = batch_handler._get_total_cores(sku)
    assert cores == 2

    sku = "Standard_HB120-32rs_v2"
    cores = batch_handler._get_total_cores(sku)
    assert cores == 32
