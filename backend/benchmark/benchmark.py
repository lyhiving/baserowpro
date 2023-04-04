#!/usr/bin/env python3

import argparse
import subprocess
from multiprocessing import Process
from pathlib import Path

import psycopg2
import requests
from django.conf import settings

DEFAULT_DB = settings.DATABASES["default"]

parser = argparse.ArgumentParser()
parser.add_argument(
    "--initdb",
    action="store_true",
    help="Should the current database be replaced with our benchmarking database?",
)
parser.add_argument(
    "--scenario",
    action="store",
    help="Execute an HTTP request which is experiencing performance issues.",
)
parser.add_argument(
    "-n",
    default=1,
    type=int,
    help="How many requests to dispatch.",
)
parser.add_argument(
    "-p",
    action="store_true",
    help="Execute the requests in parallel.",
)


class BackendScenarios:
    @classmethod
    def list_rows(cls, headers: dict):
        url = (
            f"{settings.PUBLIC_BACKEND_URL}/api/database/views/grid/1910/"
            "?limit=120&offset=0&include=row_metadata"
        )
        return requests.get(url, headers=headers)

    @classmethod
    def create_row(cls, headers: dict):
        url = f"{settings.PUBLIC_BACKEND_URL}/api/database/rows/table/450/batch/"
        return requests.post(
            url,
            json={
                "items": [
                    {
                        "field_4125": "",
                        "field_4126": "",
                        "field_4127": False,
                        "field_4151": [],
                        "field_4157": [],
                        "field_4159": False,
                        "field_4164": "",
                        "field_4165": "",
                        "field_4166": None,
                        "field_4167": "",
                        "field_4168": [],
                        "field_4170": [],
                        "field_4300": [],
                    }
                ]
            },
            headers=headers,
        )

    @classmethod
    def update_row(cls, headers: dict):
        url = f"{settings.PUBLIC_BACKEND_URL}/api/database/rows/table/450/2/"
        return requests.patch(url, {"field_4125": "foobar"}, headers=headers)

    @classmethod
    def search_rows(cls, headers: dict):
        url = (
            f"{settings.PUBLIC_BACKEND_URL}/api/database/views/grid/1910/"
            "?limit=120&offset=0&include=row_metadata&search=sarah"
        )
        return requests.get(url, headers=headers)

    @classmethod
    def read_aggregations(cls, headers: dict):
        url = f"{settings.PUBLIC_BACKEND_URL}/api/database/views/grid/1910/aggregations"
        return requests.get(url, headers=headers)


class BackendBenchmark:
    @classmethod
    def initdb(cls):
        connection = psycopg2.connect(
            database="postgres",
            user=DEFAULT_DB["USER"],
            password=DEFAULT_DB["PASSWORD"],
            host=DEFAULT_DB["HOST"],
        )
        connection.autocommit = True
        cursor = connection.cursor()
        confirm = input(
            "Calling --initdb will drop your current database, are you "
            "sure you want to do this? y/n\n"
        ).lower()
        if confirm != "y":
            return

        # Double-check the grid view many field SQL exists.
        if not Path("samples/grid-view-many-fields.sql").is_file():
            raise EnvironmentError("Please download the sample SQL.")

        try:
            cursor.execute(f"DROP DATABASE IF EXISTS {DEFAULT_DB['NAME']}")
            cursor.execute(f"CREATE DATABASE {DEFAULT_DB['NAME']}")
        except psycopg2.errors.ObjectInUse:
            raise EnvironmentError("The database cannot be re-created if it is use.")

        subprocess.run(
            f"psql -U {DEFAULT_DB['USER']} -h {DEFAULT_DB['HOST']} "
            f"{DEFAULT_DB['NAME'] } < samples/grid-view-many-fields.sql",
            shell=True,
            env={"PGPASSWORD": DEFAULT_DB["PASSWORD"]},
        )

    @classmethod
    def get_jwt(cls):
        response = requests.post(
            f"{settings.PUBLIC_BACKEND_URL}/api/user/token-auth/",
            {"email": "dev@baserow.io", "password": "testpassword"},
        )
        response.raise_for_status()
        return response.json()["access_token"]

    @classmethod
    def scenario(cls, args):
        scenarios = {
            "list-rows": BackendScenarios.list_rows,
            "create-row": BackendScenarios.create_row,
            "update-row": BackendScenarios.update_row,
            "search-rows": BackendScenarios.search_rows,
            "aggregations": BackendScenarios.read_aggregations,
        }
        if args.scenario not in scenarios:
            raise ValueError(
                f"Invalid test scenario, please use: {', '.join(scenarios.keys())}"
            )
        headers = {"Authorization": f"JWT {cls.get_jwt()}"}
        dispatch = scenarios[args.scenario]
        for _ in range(0, args.n):
            if args.p:
                process = Process(
                    target=dispatch,
                    args=(headers,),
                )
                process.start()
            else:
                dispatch(headers)


if __name__ == "__main__":
    args = parser.parse_args()
    if args.initdb:
        BackendBenchmark.initdb()
    if args.scenario:
        BackendBenchmark.scenario(args)