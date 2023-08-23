import json
import os
import numpy
import pandas
import file_functions

from constants import (
    SPECS_LIST,
    TOP_DIR,
    CLASSES, 
    PANDAS_COMPRESSION,
    running_time,
)

CLASSES_LIST = list(CLASSES)
SPECS_DATA: list[str] = []
IGNORED_SPECS = [*range(0, 40, 4), 7, 17, 18, 21, 22, 31, 39]
DUMMY_DATAFRAME = pandas.DataFrame()

def get_class_spec_full(spec_index):
    spec, icon = SPECS_LIST[spec_index]
    _class = CLASSES_LIST[spec_index//4]
    return f"{_class} {spec}".replace(' ', '-').lower()


SPECS_TO_HTML_LIST = [
    get_class_spec_full(spec_index)
    for spec_index in range(40)
]

def get_specs_data():
    if SPECS_DATA:
        return SPECS_DATA
    
    for spec_index in set(range(40)) - set(IGNORED_SPECS):
        spec, icon = SPECS_LIST[spec_index]
        _class = CLASSES_LIST[spec_index//4]
        SPECS_DATA.append({
            "class_name": _class,
            "class_html": _class.replace(' ', '-').lower(),
            "spec_name": spec,
            "spec_html": SPECS_TO_HTML_LIST[spec_index],
            "icon": icon,
        })
    return SPECS_DATA


def n_greater_than(data: numpy.ndarray, value: float):
    return int((data > value).sum())

def get_percentile(data, percentile):
    _percentile = round(numpy.percentile(data, percentile), 2)
    return {
        "p": _percentile,
        "n": n_greater_than(data, _percentile),
    }

@running_time
def _get_boss_data(df: pandas.DataFrame):
    if df.empty:
        return {}
    
    df_spec = df["s"]
    df_dps = df["u"] / df["t"]
    
    BOSS_DATA = {}
    for spec_index in range(40):
        if spec_index in IGNORED_SPECS:
            continue
        
        data_s = df_dps[df_spec == spec_index]
        if len(data_s) < 5:
            continue

        data_s = numpy.sort(data_s)
        BOSS_DATA[SPECS_TO_HTML_LIST[spec_index]] = {
            "max": {"p": max(data_s), "n": 0},
            "p99": get_percentile(data_s, 99),
            "p95": get_percentile(data_s, 95),
            "p90": get_percentile(data_s, 90),
            "p75": get_percentile(data_s, 75),
            "p50": get_percentile(data_s, 50),
            "p10": get_percentile(data_s, 10),
            "all": {"p": 0, "n": len(data_s)},
        }
    return BOSS_DATA

def get_boss_top_file(server: str=None, boss: str=None, mode: str=None):
    if not server:
        server = "Lordaeron"
    if not boss:
        boss = "The Lich King"
    if not mode:
        mode = "25H"

    server_folder = os.path.join(TOP_DIR, server)
    return os.path.join(server_folder, f"{boss} {mode}.{PANDAS_COMPRESSION}")

@running_time
def _from_pickle(fname) -> pandas.DataFrame:
    try:
        return pandas.read_pickle(fname, compression=PANDAS_COMPRESSION)
    except FileNotFoundError:
        return DUMMY_DATAFRAME

def _get_boss_data_cache(boss_file):
    def inner():
        df = _from_pickle(boss_file)
        data = _get_boss_data(df)
        return json.dumps(data)
    return file_functions.cache_file_until_new(boss_file, inner)

def get_boss_data_wrap():
    CACHE = {}
    def inner(server: str=None, boss: str=None, mode: str=None) -> str:
        boss_file = get_boss_top_file(server, boss, mode)
        f = CACHE.get(boss_file)
        if f is None:
            f = _get_boss_data_cache(boss_file)
            CACHE[boss_file] = f
        return f()
    return inner

get_boss_data = get_boss_data_wrap()
