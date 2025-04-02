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

Ensure you save the following environment variables:

```python
MONGODB_USERNAME
MONGODB_PASSWORD
MONGODB_CONNECTIONSTRING
```

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

`dlt` or data load tool is a lightweight python library primarily for the 'E' in ETL.

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
 
## Dagster + dlt

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

