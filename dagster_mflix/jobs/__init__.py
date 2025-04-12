from dagster import AssetSelection, define_asset_job

movies_job = define_asset_job(
    name="movies_job",
    selection=AssetSelection.all() - AssetSelection.groups("mongodb")
)