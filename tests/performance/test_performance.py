import cProfile
import dataclasses
import logging
import pstats
import random
import timeit
import uuid
from functools import partial

import slycache

service_cache = slycache.with_defaults(namespace="performance")


log = logging.getLogger("slycache")
log.setLevel(logging.ERROR)


@dataclasses.dataclass
class CacheObject:
    id: str


@service_cache.cache_result("{obj_id}")
def getter(obj_id):
    return CacheObject(obj_id)


def base_line_getter(cache):
    """call the underlying cache directly"""
    def baseline(obj_id):
        res = cache.get(obj_id)
        if not res:
            res = CacheObject(obj_id)
            cache.set(str(obj_id), res)
        return res
    return baseline


def _run_perf_test(cache, baseline, actual, item_count=10000, repeat_count=5, run_count=5):
    ids, init_cache = _prep_cache(cache, item_count)

    def run(test_func):
        for obj_id in ids:
            test_func(obj_id)

    baseline_func = baseline(cache)

    baseline_timer = timeit.Timer(partial(run, baseline_func), init_cache)
    actual_timer = timeit.Timer(partial(run, actual), init_cache)

    baseline_times = baseline_timer.repeat(repeat_count, run_count)
    actual_times = actual_timer.repeat(repeat_count, run_count)
    actual_no_baseline = [pair[0] - pair[1] for pair in zip(actual_times, baseline_times)]

    return actual_no_baseline, baseline_times


def test_get_perf(default_cache):
    repeat_count = 3
    run_count = 5
    item_count = 10000
    actual, baseline = _run_perf_test(
        default_cache, base_line_getter, getter,
        item_count=item_count, repeat_count=repeat_count, run_count=run_count
    )

    def avg(times):
        return sum(times) / run_count

    avg_actual = avg(actual)
    avg_baseline = avg(baseline)

    print(f"\nAverage baseline: {avg_baseline}")
    print(f"Average slycache: {avg_actual}")
    print(f"Performance multiplier: {avg_actual/avg_baseline}")
    assert avg_actual < avg_baseline * 20, (avg_actual/avg_baseline)


def test_get_cprofile(default_cache):
    ids, init_cache = _prep_cache(default_cache)
    init_cache()

    with cProfile.Profile() as prof:
        for obj_id in ids:
            getter(obj_id)

    stats = pstats.Stats(prof)
    stats.sort_stats('cumulative').print_stats()


def _prep_cache(cache, item_count=10000):
    ids = [
        uuid.uuid4().hex for i in range(item_count)
    ]

    def init_cache():
        cache.clear()
        cache.init({
            obj_id: CacheObject(obj_id) for obj_id in ids[:item_count//2]
        })

    random.shuffle(ids)
    return ids, init_cache
