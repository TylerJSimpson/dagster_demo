from dagster import Definitions, load_assets_from_modules
from dagster_embedded_elt.dlt import DagsterDltResource
from .assets import mongodb

mongodb_assets = load_assets_from_modules([mongodb])

defs = Definitions(
    assets=[*mongodb_assets],
    resources={
        "dlt": DagsterDltResource(),
    }
)