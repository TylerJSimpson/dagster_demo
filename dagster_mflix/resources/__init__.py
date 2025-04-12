from dagster import EnvVar
from dagster_embedded_elt.dlt import DagsterDltResource
from dagster_snowflake import SnowflakeResource


snowflake_resource = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse="dagster_wh",
    database="dagster_db",
    schema="mflix",
    role="dagster_role",
)

dlt_resource = DagsterDltResource()