from __future__ import division

import unittest

import schedcat.model.tasks as tasks
import schedcat.model.resources as resources
import schedcat.overheads.simple_locking as simple_locking
import schedcat.locking.bounds as bounds
import schedcat.locking.model as lmodel


class LockingWithOverhead(unittest.TestCase):
    def setUp(self):
        """
        Initilize a dict of SpinLocks with different overheads.
        """
        self.lock = {
            'optimispinlock': lmodel.Unordered(79),
            'spinlock': lmodel.Unordered(118),
            'mcslock': lmodel.Fifo(148),
            'ticketlock': lmodel.Fifo(179),
            'prioritylock': lmodel.Priority_Unordered(193),
        }

    def binary_test_function(self, period):
        """
        Test if the generated Taskset of a given period is schedulable.

        Uses the rta analysis.
        """
        taskset = generate_taskset(period)
        return simple_locking.is_schedulable(taskset)

    def test_schedulability(self):
        results = []
        for name, lock in self.lock.iteritems():
            simple_locking.default_spinlock = lock
            best_period = binary_search(self.binary_test_function)
            results.append( (name, best_period) )

        # Display the results (debugging)
        results = sorted(results, key=lambda (_,x):x)
        for name, score in results:
            print(name + ': ' + str(score))


def generate_taskset(period):
    """
    Generate a Taskset with a given period for every task
    """
    duration = 500
    ts = tasks.TaskSystem([
        tasks.SporadicTask(duration, period),
        tasks.SporadicTask(duration, period),
        tasks.SporadicTask(duration, period),
        ])

    resources.initialize_resource_model(ts)
    # Assumes taskset has already been sorted and ID'd in priority order.
    bounds.assign_fp_preemption_levels(ts)

    # tasks resource duration
    for _ in range(10):
        ts[0].resmodel[0].add_request(50)
    ts[1].resmodel[0].add_request(50)
    ts[2].resmodel[0].add_request(50)

    # Set one task per partition (and one partition per core)
    for i, t in enumerate(ts):
        t.partition = i
        t.response_time = t.period
    return ts

def binary_search(test_function, lo=1, hi=100000):
    """
    Compute the smallest value satisfying the test_function

    It uses a binary search approach.
    Search between lo and hi values.
    """
    while lo < hi:
        mid = (lo+hi)//2
        if not test_function(mid):
            lo = mid+1
        else:
            hi = mid
    return lo
