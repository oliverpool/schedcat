from __future__ import division

import unittest

import schedcat.model.tasks as tasks
import schedcat.model.resources as resources
import schedcat.overheads.simple_locking as simple_locking
import schedcat.sched.edf as edf

import schedcat.locking.bounds as bounds

import schedcat.locking.model as lmodel

from schedcat.sched.fp import is_schedulable

class LockingWithOverhead(unittest.TestCase):
    def setUp(self):
        duration = 500
        period = 700
        self.ts = tasks.TaskSystem([
            tasks.SporadicTask(duration, period),
            tasks.SporadicTask(duration, period),
            tasks.SporadicTask(duration, period),
            ])

        resources.initialize_resource_model(self.ts)
        # Assumes taskset has already been sorted and ID'd in priority order.
        bounds.assign_fp_preemption_levels(self.ts)


        # tasks resource duration
        self.ts[0].resmodel[0].add_request(20)
        self.ts[1].resmodel[0].add_request(20)
        self.ts[2].resmodel[0].add_request(20)

        # put all tasks in the same partition (global scheduling)
        for i, t in enumerate(self.ts):
            t.partition = 0
            t.response_time = t.cost


    def test_schedulability(self):
        cpus = 3

        # Example of lock overheads
        spinlock = lmodel.Unordered(60)
        mcslock = lmodel.Fifo(94)
        ticketlock = lmodel.Fifo(74)
        prioritylock = lmodel.Priority_Unordered(127)

        mylock = mcslock

        simple_locking.protect_resource_with(0, mylock)

        self.ts = simple_locking.charge_spinlock_overheads(self.ts)
        fixed_point_reached, new_ts = simple_locking.stable_schedule(self.ts, cpus, mylock)

        self.assertTrue(fixed_point_reached)
