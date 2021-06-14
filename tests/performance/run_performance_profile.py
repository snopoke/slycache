import cProfile
import dataclasses
import logging
import pstats
import random
import timeit
import uuid
from functools import partial
from statistics import stdev

import slycache

NAMESPACE = "perf"
service_cache = slycache.with_defaults(namespace=NAMESPACE)


log = logging.getLogger("slycache")
log.setLevel(logging.ERROR)


@dataclasses.dataclass
class CacheObject:
    id: str


@service_cache.cache_result("{obj_id}")
def cache_result(obj_id):
    return CacheObject(obj_id)


@service_cache.cache_put("{obj_id}")
def cache_put(obj_id):
    return obj_id


@service_cache.cache_remove("{obj_id}")
def cache_remove(obj_id):
    return obj_id


def base_line_cache_result(cache):
    """call the underlying cache directly"""
    def baseline(obj_id):
        key = f"{NAMESPACE}:{obj_id}"
        res = cache.get(key)
        if not res:
            res = CacheObject(key)
            cache.set(key, res)
        return res
    return baseline


def baseline_cache_put(cache):

    def baseline(obj_id):
        key = f"{NAMESPACE}:{obj_id}"
        cache.set(key, obj_id)
        return obj_id

    return baseline


def baseline_remove(cache):

    def baseline(obj_id):
        key = f"{NAMESPACE}:{obj_id}"
        cache.delete(key)
        return obj_id

    return baseline


def _run_perf_test(baseline, actual, args, setup, repeat_count=5, run_count=5):
    def run(test_func):
        for arg in args:
            test_func(arg)

    baseline_timer = timeit.Timer(partial(run, baseline), setup)
    actual_timer = timeit.Timer(partial(run, actual), setup)

    baseline_times = baseline_timer.repeat(repeat_count, run_count)
    actual_times = actual_timer.repeat(repeat_count, run_count)
    actual_no_baseline = [pair[0] - pair[1] for pair in zip(actual_times, baseline_times)]

    return actual_no_baseline, baseline_times


def _test_performance(name, cache, baseline, actual, prime_cache: bool, check_hits=True):
    repeat_count = 10
    run_count = 1

    cache_size = 10000
    if prime_cache:
        prime_count = cache_size
    else:
        prime_count = 0

    ids, setup = _prep_cache(cache, cache_size, prime_count)
    actual, baseline = _run_perf_test(
        baseline, actual,
        ids, setup, repeat_count=repeat_count, run_count=run_count
    )

    if check_hits:
        hits_misses = f"\n[{name}] Cache hits vs misses {cache.hits} : {cache.misses}"
        if prime_cache:
            assert (cache.hits, cache.misses) == (cache_size, 0), hits_misses
        else:
            assert (cache.hits, cache.misses) == (0, cache_size), hits_misses

    def avg(times):
        return sum(times) / run_count

    avg_actual = avg(actual)
    avg_baseline = avg(baseline)

    print(f"\n[{name}] Operation count: {cache_size * run_count}")
    print(f"[{name}] Average baseline: {avg_baseline:.4f}, stdev: {stdev(baseline):.4f}")
    print(f"[{name}] Average slycache: {avg_actual:.4f}, stdev: {stdev(actual):.4f}")
    print(f"[{name}] Performance multiplier: {avg_actual/avg_baseline}")
    # assert avg_actual < avg_baseline * 20, (avg_actual/avg_baseline)


def test_get_only(default_cache):
    baseline = base_line_cache_result(default_cache)
    _test_performance("get", default_cache, baseline, cache_result, prime_cache=True)


def test_get_and_set(default_cache):
    baseline = base_line_cache_result(default_cache)
    _test_performance("get_set", default_cache, baseline, cache_result, prime_cache=False)


def test_put(default_cache):
    baseline = baseline_cache_put(default_cache)
    _test_performance("set", default_cache, baseline, cache_put, prime_cache=False, check_hits=False)


def test_remove(default_cache):
    baseline = baseline_remove(default_cache)
    _test_performance("delete", default_cache, baseline, cache_remove, prime_cache=True, check_hits=False)


def test_get_cprofile(default_cache):
    ids, init_cache = _prep_cache(default_cache)
    init_cache()

    with cProfile.Profile() as prof:
        for obj_id in ids:
            cache_result(obj_id)

    stats = pstats.Stats(prof)
    stats.sort_stats('cumulative').print_stats()


def _prep_cache(cache, item_count=10000, cached_count=2500):
    ids = [
        uuid.uuid4().hex for i in range(item_count)
    ]

    def init_cache():
        cache.clear()
        cache.init({
            f"{NAMESPACE}:{obj_id}": CacheObject(obj_id) for obj_id in ids[:cached_count]
        })

    random.shuffle(ids)
    return ids, init_cache
