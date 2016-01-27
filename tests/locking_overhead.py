from __future__ import division

import unittest

import schedcat.model.tasks as tasks
import schedcat.model.resources as resources
import schedcat.overheads.simple_locking as simple_locking
import schedcat.locking.bounds as bounds
import schedcat.locking.model as lmodel

def generate_taskset(period, duration, cs_duration, cs_number):
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

    ts[0].resmodel[0].add_request(cs_duration // 2)
    # tasks resource duration
    for _ in range(cs_number):
        ts[0].resmodel[0].add_request(cs_duration)
        ts[1].resmodel[0].add_request(cs_duration)
        ts[2].resmodel[0].add_request(cs_duration)

    # Set one task per partition (and one partition per core)
    for i, t in enumerate(ts):
        t.partition = i
        t.response_time = t.period
    return ts

class LockingWithOverhead(unittest.TestCase):
    def setUp(self):
        """
        Initilize a dict of SpinLocks with different overheads.
        """
        self.lock = {
            'unordered': lmodel.Unordered(10),
            'fifo': lmodel.Fifo(20),
            'prio': lmodel.Priority_Unordered(30),
            'priofifo': lmodel.Priority_Fifo(40),
        }

    def test_schedulability(self):
        period = 15000
        duration = 5000
        cs_duration = 1000
        cs_number = 1
        taskset = generate_taskset(period, duration, cs_duration, cs_number)
        self.assertTrue(simple_locking.is_schedulable(taskset))



        duration = 6000
        cs_duration = 2000
        # Depending on the lock, the taskset is schedulable or not
        simple_locking.default_spinlock = self.lock['unordered']
        taskset = generate_taskset(period, duration, cs_duration, cs_number)
        self.assertFalse(simple_locking.is_schedulable(taskset))

        simple_locking.default_spinlock = self.lock['fifo']
        taskset = generate_taskset(period, duration, cs_duration, cs_number)
        self.assertTrue(simple_locking.is_schedulable(taskset))
