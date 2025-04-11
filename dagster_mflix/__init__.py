from dagster import Definitions, load_assets_from_modules, EnvVar
from dagster_embedded_elt.dlt import DagsterDltResource
from .assets import mongodb, movies
from dagster_snowflake import SnowflakeResource

mongodb_assets = load_assets_from_modules([mongodb])
movies_assets = load_assets_from_modules([movies], group_name="movies")

snowflake = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse="dagster_wh",
    database="dagster_db",
    schema="mflix",
    role="dagster_role"
)

defs = Definitions(
    assets=[*mongodb_assets, *movies_assets],
    resources={
        "dlt": DagsterDltResource(),
        "snowflake": snowflake
    }
)