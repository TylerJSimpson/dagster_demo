# dagster_demo

## Python

3.12+ works well with current Mongo DB stable version as of 3/31/2025.

```bash
python3.12 -m venv .venv
```

```bash
source .venv/bin/activate
```

## Mongo DB (Datasource)

Signup: https://cloud.mongodb.com/

Ensure you save the username, password, and connection string. The connection string is all that is needed in env variables.

Add the `sample_mflix` dataset.

```bash
python -m pip install "pymongo[srv]"==3.12
```

## Snowflake (Warehouse)

Signup: https://app.snowflake.com/

Press the `+` sign.

*Note below `granumtech` you will need to replace this with the username you used on signup*

```SQL
use role accountadmin;

create warehouse if not exists dagster_wh with warehouse_size='x-small';
create database if not exists dagster_db;
create role if not exists dagster_role;

grant usage on warehouse dagster_wh to role dagster_role;
grant role dagster_role to user granumtech;
grant all on database dagster_db to role dagster_role;
```

## Dagster (Orchestration)

Install packages:

```bash
pip install dagster==1.7.7 dagster-embedded-elt==0.23.7
```

Create new Dagster project:

```bash
dagster project scaffold --name dagster_mflix --ignore-package-conflict
```

*I was getting errors so added the `--ignore-package-conflict` as suggested by CLI.

Dagster architecture:

```
├── dagster_mflix
│   ├── README.md
│   ├── dagster_mflix
│   │   ├── __init__.py
│   │   └── assets.py
│   ├── dagster_mflix_tests
│   │   ├── __init__.py
│   │   └── test_assets.py
│   ├── pyproject.toml
│   ├── setup.cfg
│   └── setup.py
```

Update `setup.py` to include the required packages:

```python
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
```

to:

```python
    install_requires=[
        "dagster==1.7.7",
        "dagster-cloud==1.7.7",
        "dagster-snowflake==0.23.7",
        "pymongo>=4.3.3",
        "dlt[snowflake]>=0.3.5",
        "scikit-learn==1.5.0"
    ],
```

Now to install the dependencies:

```bash
pip install -e ".[dev]"
```

We are using `-e` so that changes to the code will be immediately reflected and `[dev]` is specifying we also want the packages in that portion of the `setup.py` file.

## dlt (Extraction)

`dlt` or data load tool is a lightweight python framework for connection data sources. dlt offers boilerplates to most common connections like in our example MongoDB and Snowflake.

We have already installed the package previously `dlt[snowflake]>=0.3.5`. Now we need to init

```bash
cd dagster_mflix
mkdir dlt
cd dlt
dlt init mongodb snowflake
```

Note that when you initialize you can specify the source and sink i.e. `mongodb snowflake` above. This will automatically create a basic project structure.

A `requirements.txt` will be created in the project directory. Ensure you run those requirements.

```bash
pip install -r requirements.txt
```

All we really need out of the dlt directory at this point is the `mongodb` folder that was created.

```bash
cp -r mongodb ../dagster_mflix
rm -r mongodb
```
 
## Dagster: dlt -> snowflake (Extraction)

### Dagster + dlt

```bash
cd ../dagster_mflix
mkdir assets
cd assets
touch mongodb.py
```

[mongodb.py](/dagster_mflix/dagster_mflix/assets/mongodb.py)

Update dagster_mflix/[__init__.py](/dagster_mflix/dagster_mflix/__init__.py) from:

```python
from dagster import Definitions, load_assets_from_modules

from . import assets

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
)

```

to:

```python
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
```

Remove original `assets.py`:

```bash
rm -r assets.py
```

Create environment file `.env` in main directory:

```bash
touch .env
```

Start Dagster web UI:

```bash
dagster dev
```

In the UI go ahead and go to the `Assets` tab and `Materialize`.

### Dagster + Snowflake

in `assets` create [movies.py](/dagster_mflix/assets/movies.py).

Our goal is to create 3 tables (assets) in dagster: `user engagement`, `top movies by month`, `top movies by engagement`

1st we want to start by creating functions and labeling them as dagster assets

```python
from dagster_snowflake import SnowflakeResource
from dagster import asset
import os
import pandas as pd
import matplotlib.pyplot as plt

@asset
def user_engagement(snowflake: SnowflakeResource) -> None:
    pass

@asset
def top_movies_by_month(snowflake: SnowflakeResource) -> None:
    pass

@asset
def top_movies_by_engagement(snowflake: SnowflakeResource) -> None:
    pass
```

Then specify dependencies:

```python
@asset(
    deps=["dlt_mongodb_comments","dlt_mongodb_embedded_movies"]
)
def user_engagement(snowflake: SnowflakeResource) -> None:
    pass

@asset(
    deps=["dlt_mongodb_embedded_movies"]
)
def top_movies_by_month(snowflake: SnowflakeResource) -> None:
    pass

@asset(
    deps=["user_engagement"]
)
def top_movies_by_engagement(snowflake: SnowflakeResource) -> None:
    pass
```

Now we want to make sure we update our [__init__.py](/dagster_mflix/__init__.py) to include the Snowflake details as well as the new assets we created:

```python
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
```

We are using `EnvVar` as opposed to `os.environ.get` because dagster handles them differently and this approach hides it from the interface.

Notice in our `movies.py` the `snowflake: SnowflakeResource`:

```python
def user_engagement(snowflake: SnowflakeResource) -> None:
```

This is linked to our resource definitions in `__init__.py`:

```python
    resources={
        "dlt": DagsterDltResource(),
        "snowflake": snowflake
```

Now we can add code to our `movies.py` to actually process the data instead of just pass for our other methods [movies.py](/dagster_mflix/assets/movies.py).

Note you can see the function descriptions in the code i.e.

```python
    """
    Movie titles and the number of user engagement (i.e. comments)
    """
```
Dagster will automatically pick these up and set them as the description in the UI.

### Dagster resources

To follow the **DRY** principal we want to utilize Dagster **resources** so we can avoid repeating resources such as connector code like for snowflake in our example.

We can create a **resources** folder and copy the snowflake connection code from our main \_\_init___.py to the \_\_init___.py here.

Now our main \_\_init___.py definitions file will look like this

```python
from dagster import Definitions, load_assets_from_modules
from .assets import mongodb, movies, adhoc
from .resources import snowflake_resource, dlt_resource

mongodb_assets = load_assets_from_modules([mongodb])
movies_assets = load_assets_from_modules([movies], group_name="movies")

defs = Definitions(
    assets=[*mongodb_assets, *movies_assets],
    resources={
        "dlt": dlt_resource,
        "snowflake": snowflake_resource
    }
)
```

And our new **resources** \_\_init__.py file like this:

```python
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
```

### Schedules and Jobs

Instead of manually materializing let's look at **schedules** and **jobs**.

**schedules** are the traditional method of automation and represent a fixed time interval. They include a **cron expression** and a **job**.

**jobs** specify which assets to run on the **schedule** at the time specified on the **cron expression**.

Create a **jobs** folder with an [\_\_init__.py](/dagster_mflix/jobs/__init__.py) as well as a **schedules** folder with an [\_\_init__.py](/dagster_mflix/schedules/__init__.py).

We also need to update our definitions function in our main [\_\_init__.py](/dagster_mflix/__init__.py) to include schedules a jobs.

Currently:
```python
defs = Definitions(
    assets=[*mongodb_assets, *movies_assets],
    resources={
        "dlt": dlt_resource,
        "snowflake": snowflake_resource
    }
)
```

Update:
```python
defs = Definitions(
    assets=[*mongodb_assets, *movies_assets],
    resources={
        "dlt": dlt_resource,
        "snowflake": snowflake_resource
    },
    jobs=[movies_job],
    schedules=[movies_schedule]
)
```

Now on the Dagster UI under **Overview** then **Schedules** you will see the newly created schedule and can turn it on.

### Partitions

**Partitions** can be used to backfill your DAGs. Paritions are collections of chunks of the data. This is helpful for parallel processing. Backfilling is the process of running **partitions** for assets or ops that either don't exist or updating existing records.

Again let's create a new folder **partitions** with [\_\_init__.py](/dagster_mflix/partitions/__init__.py).

Then we need to update our assets to apply our partitions.

```python
from ..partitions import monthly_partition
```

Then you can update the asset to include the partition.

```python
@asset(
    deps=["dlt_mongodb_embedded_movies"],
    partitions_def=monthly_partition
)
```

Inside the asset function you can then include the partition key.

```python
    partition_date = context.partition_key
```

And use it in your query f string.

```sql
        where released >= '{partition_date}'::date
        and released < '{partition_date}'::date + interval '1 month'
```

### Sensors and Auto Materialiation

**Sensors** are definitions that allow you to instigate runs based on some external state change. For example, run when a file hits an S3 bucket.

Again we will create a **sensors** folder with [\_\_init__.py](/dagster_mflix/sensors/__init__.py).

You will notice in the sensor we included a new job which needs added to the jobs init file:

```python
adhoc_job = define_asset_job(
    name="adhoc_job",
    selection=AssetSelection.assets(["movie_embeddings"])
)
```

Now we need to create the new asset [adhoc.py](/dagster_mflix/assets/adhoc.py).

Note that we now need to update the assets and add the sensors in our main [\_\_init__.py](/dagster_mflix/__init__.py).

```python
from dagster import Definitions, load_assets_from_modules

from .assets import mongodb, movies, adhoc
from .resources import snowflake_resource, dlt_resource
from .jobs import movies_job, adhoc_job
from .schedules import movies_schedule
from .sensors import adhoc_sensor


mongodb_assets = load_assets_from_modules([mongodb])
movies_assets = load_assets_from_modules([movies], group_name="movies")
adhoc_assets = load_assets_from_modules([adhoc], group_name="ad_hoc")

defs = Definitions(
    assets=[*mongodb_assets, *movies_assets, *adhoc_assets],
    resources={
        "dlt": dlt_resource,
        "snowflake": snowflake_resource
    },
    jobs=[movies_job, adhoc_job],
    schedules=[movies_schedule],
    sensors=[adhoc_sensor]
)
```

Now how do we actually get this new ad_hoc movie_embeddings to run?

Recall:

```python
class AdhocConfig(Config):
    filename: str
    ratings: str
```

So every 30 seconds this is going to poll if there is a file that exists that has this ratings data.

If we create [ratings.json](/dagster_mflix/adhoc/ratings.json) and specify the rating and turn the sensor on you will see it will matieralize the tnse data in the data folder.

### Auto-materialization

This is a new feature. It allows you to specify conditions under which assets should be materialized instead of defining imperative workflows.

The main way it is used is in asset definitions for **eager** scenarios i.e. it will materialize when upstream assets materialize.

```python
from dagster import AutoMaterializePolicy

auto_materialize_poly = AutoMaterializePolicy.eager()
```

Now check out the improved [movies.py](/dagster_mflix/assets/movies.py) where we have added this auto materialization policy to top_movies_by_engagement. This means if user_engagement just before it materializes then this asset will as well.