"""The data model and data of the Atoti tutorial.

See https://docs.activeviam.com/engine/python-sdk/6.2/getting_started/tutorial/tutorial
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import atoti as tt
import pandas as pd
from opentelemetry import trace

DATA_DIRECTORY: Final = Path(__file__).parent / "data"

_TRACER: Final = trace.get_tracer(__name__)


def create_data_model(session: tt.Session, /) -> tt.Cube:
    with _TRACER.start_as_current_span("load tables"):
        sales_table = session.read_csv(
            DATA_DIRECTORY / "sales.csv", keys={"Sale ID"}, table_name="Sales"
        )
        products_table = session.read_csv(
            DATA_DIRECTORY / "products.csv", keys={"Product"}, table_name="Products"
        )
        shops_table = session.read_csv(
            DATA_DIRECTORY / "shops.csv", keys={"Shop ID"}, table_name="Shops"
        )

    with _TRACER.start_as_current_span("join tables"):
        sales_table.join(
            products_table, sales_table["Product"] == products_table["Product"]
        )
        sales_table.join(shops_table, sales_table["Shop"] == shops_table["Shop ID"])

    with _TRACER.start_as_current_span("create cube"):
        cube = session.create_cube(sales_table)

    h, l, m = cube.hierarchies, cube.levels, cube.measures

    with _TRACER.start_as_current_span("define measures"):
        m["Purchase price.VALUE"] = tt.agg.single_value(
            products_table["Purchase price"]
        )
        m["Max price"] = tt.agg.max(sales_table["Unit price"])
        m["Amount.SUM"] = tt.agg.sum(
            sales_table["Quantity"] * sales_table["Unit price"]
        )
        m["Amount.MEAN"] = tt.agg.mean(
            sales_table["Quantity"] * sales_table["Unit price"],
        )
        cost = tt.agg.sum(
            m["Quantity.SUM"] * tt.agg.single_value(products_table["Purchase price"]),
            scope=tt.OriginScope({l["Product"]}),
        )
        m["Margin"] = m["Amount.SUM"] - cost
        m["Margin rate"] = m["Margin"] / m["Amount.SUM"]
        m["Cumulative amount"] = tt.agg.sum(
            m["Amount.SUM"],
            scope=tt.CumulativeScope(l["Date"]),
        )
        m["Average amount per shop"] = tt.agg.mean(
            m["Amount.SUM"],
            scope=tt.OriginScope({l["Shop"]}),
        )

    with _TRACER.start_as_current_span("define hierarchies"):
        h["Product"] = [l["Category"], l["Sub category"], l["Product"]]
        del h["Category"]
        del h["Sub category"]

        h["Geography"] = [
            shops_table["Country"],
            shops_table["State or region"],
            shops_table["City"],
        ]
        del h["Country"]
        del h["State or region"]
        del h["City"]
        h["Geography"].dimension_name = "Location"

        m["Parent category amount"] = tt.parent_value(
            m["Amount.SUM"],
            degrees={h["Products", "Product"]: 1},
        )
        m["Percent of parent amount"] = m["Amount.SUM"] / m["Parent category amount"]

    with _TRACER.start_as_current_span("polish cube"):
        del m["Unit price.SUM"]
        m["Parent category amount"].visible = False
        for measure in [
            m["Amount.MEAN"],
            m["Amount.SUM"],
            m["Average amount per shop"],
            m["Cumulative amount"],
            m["Percent of parent amount"],
        ]:
            measure.folder = "Amount"
        m["Percent of parent amount"].formatter = "DOUBLE[0.00%]"
        m["Margin rate"].formatter = "DOUBLE[0.00%]"

    with _TRACER.start_as_current_span("create simulations"):
        _create_source_simulation(products_table)
        _create_parameter_simulation(cube, sales_table)

    return cube


def _create_source_simulation(products_table: tt.Table, /) -> None:
    products_df = pd.read_csv(DATA_DIRECTORY / "products.csv")
    better_prices = {
        "TAB_0": 180.0,
        "TAB_1": 250.0,
        "CHA_2": 40.0,
        "BED_3": 110.0,
        "BED_4": 210.0,
    }
    for product, purchase_price in better_prices.items():
        products_df.loc[products_df["Product"] == product, "Purchase price"] = (
            purchase_price
        )
    products_table.scenarios["Cheaper purchase prices"].load(products_df)


def _create_parameter_simulation(cube: tt.Cube, sales_table: tt.Table, /) -> None:
    l, m = cube.levels, cube.measures

    country_simulation = cube.create_parameter_simulation(
        "Country Simulation",
        levels=[l["Country"]],
        measures={"Country parameter": 1.0},
    )
    country_simulation += ("France Crisis", "France", 0.80)
    country_simulation += ("US boost", "USA", 1.15)

    m["Quantity.SUM"] = tt.agg.sum(
        tt.agg.sum(sales_table["Quantity"]) * m["Country parameter"],
        scope=tt.OriginScope({l["Country"]}),
    )
    m["Amount.SUM"] = tt.agg.sum(
        tt.agg.sum(sales_table["Unit price"] * sales_table["Quantity"])
        * m["Country parameter"],
        scope=tt.OriginScope({l["Country"]}),
    )
