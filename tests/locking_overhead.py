from __future__ import division
from collections import OrderedDict

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
        self.lock = OrderedDict({
            'optimispinlock': lmodel.Unordered(79),
            'spinlock': lmodel.Unordered(118),
            'ticketlock': lmodel.Fifo(148),
            'mcslock': lmodel.Fifo(179),
            'prioritylock': lmodel.Priority_Unordered(193),
            'idealfifo': lmodel.Fifo(0),
            #'priofifo': lmodel.Priority_Fifo(148), # Not measured
        })

    def test_schedulability(self):
        """
        Test some schedulability parameters
        """

        # See 'iter_durations' for details
        cases = [
            'cs_duration', # different critical section durations
            'cs_number', # different critical section number
            'cs_subdiv', # subdivide a large critical section into smaller chunks
        ]

        for filename in cases:
            sheet = self.schedulability_results(filename)
            #print('\n'.join(','.join(map(str, line)) for line in sheet))
            save_results(filename, sheet)

    def schedulability_results(self, filename):
        """
        Generate an array of the schedulability results for the different lock
        types.

        The first line contains the titles:
        - filename (cs_number/duration/subdiv)
        - the different lock types
        - the critical section duration
        The following lines contain the smallest period for which the task set
        is schedulable (the lower the better)
        """
        results = []

        line = [filename]
        for name, lock in self.lock.iteritems():
            line.append(name)
        line.append('cs_duration')
        results.append(line)
        for x, duration, cs_duration, cs_number in iter_durations(filename):
            line = [x]
            test_function = generate_binary_test_function(duration, cs_duration, cs_number, filename)
            for name, lock in self.lock.iteritems():
                simple_locking.default_spinlock = lock
                best_period = binary_search(test_function)
                line.append(best_period)
            line.append(cs_duration)
            results.append(line)
        return results

def iter_durations(case='cs_subdiv'):
    """Return the task set duration settings:

    x, duration, cs_duration, cs_number
    <x> depends on the case (will be used as x-axis)
    """
    duration = 15000
    if case == 'cs_subdiv':
        """Subdivide an initial critical section into smaller chunks"""
        cs_duration = 8000
        for cs_number in range(1, 101, 3):
            yield cs_number, duration, cs_duration//cs_number, cs_number
    elif case == 'cs_number':
        """Increase the number of critical sections"""
        cs_duration = 50
        for cs_number in range(21):
            yield cs_number, duration, cs_duration, cs_number
    elif case == 'cs_duration':
        """Increase the duration of the critical section(s)"""
        cs_number = 1
        for cs_duration in range(0, 401, 10):
            yield cs_duration, duration, cs_duration, cs_number

def generate_taskset(period, duration, cs_duration, cs_number, filename):
    """
    Generate a Taskset with a given period for every task
    """
    ts = tasks.TaskSystem([
        tasks.SporadicTask(duration, period),
        tasks.SporadicTask(duration, period),
        tasks.SporadicTask(duration, period),
        ])

    resources.initialize_resource_model(ts)
    # Assumes taskset has already been sorted and ID'd in priority order.
    bounds.assign_fp_preemption_levels(ts)

    if filename in ['cs_number', 'cs_duration']:
        # Asymmetry needed to emphasize some results
        ts[0].resmodel[0].add_request(cs_duration // 2)
    # tasks resource duration
    for i in range(cs_number):
        ts[0].resmodel[0].add_request(cs_duration)
        ts[1].resmodel[0].add_request(cs_duration)
        ts[2].resmodel[0].add_request(cs_duration)

    # Set one task per partition (and one partition per core)
    for i, t in enumerate(ts):
        t.partition = i
        t.response_time = t.period
    return ts

def generate_binary_test_function(duration, cs_duration, cs_number, filename):
    """
    Test if the generated Taskset of a given period is schedulable.

    Uses the rta analysis.
    """
    def binary_test_function(period):
        taskset = generate_taskset(period, duration, cs_duration, cs_number, filename)
        return simple_locking.is_schedulable(taskset)
    return binary_test_function

def binary_search(test_function, lo=1, hi=3000000):
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

def save_results(filename, results):
    """
    Save the results to a .dat file for LaTeX integration
    """
    filepath = filename + '.dat'
    with open(filepath, 'w') as thefile:
        for line in results:
            thefile.write(','.join(map(str, line)) + '\n')
