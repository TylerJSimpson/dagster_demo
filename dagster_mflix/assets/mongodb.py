from dagster import AssetExecutionContext
from dagster_embedded_elt.dlt import DagsterDltResource, dlt_assets
import dlt
from ..mongodb import mongodb

mflix = mongodb(
    database="sample_mflix"
).with_resources( # Note we are just picking 2 of the tables from the database
    "comments",
    "embedded_movies"
)

@dlt_assets( # Python decorator
    dlt_source=mflix, # Source
    dlt_pipeline=dlt.pipeline(
        pipeline_name="local_mongo",
        destination="snowflake", # Destination
        dataset_name="mflix",
    ),
    name="mongodb",
    group_name="mongodb"
)
def dlt_asset_factory(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context, write_disposition="merge")