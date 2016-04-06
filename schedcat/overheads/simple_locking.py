from schedcat.locking.model import Unordered
import schedcat.model.tasks as tasks
import schedcat.sched.fp as fp

# Store the spinlock associated to the resources
resource2spinlock = {}
default_spinlock = Unordered()

def protect_resource_with(resource_id, spinlock):
    """ Associate the resource_id with the spinlock (for overhead contribution)"""
    global resource2spinlock
    resource2spinlock[resource_id] = spinlock

def get_resource_spinlock(resource_id):
    """ Get the spinlock associated to a resource_id"""
    return resource2spinlock.get(resource_id, default_spinlock)

def charge_spinlock_overheads(tasks):
    """ Inflate each request and task execution cost
    depending on critical and non-critical overhead of the spinlock"""
    for t in tasks:
        extra_wcet = 0

        for resource_id in t.resmodel:
            spinlock = get_resource_spinlock(resource_id)
            resource = t.resmodel[resource_id]

            if resource.max_reads:
                resource.max_read_length += spinlock.critical_overhead

            if resource.max_writes:
                resource.max_write_length += spinlock.critical_overhead

            extra_wcet += (resource.max_reads + resource.max_writes) * spinlock.total_overhead

        t.cost += extra_wcet
    return tasks

def iter_partitions_ts(taskset):
    """ Generate a Taskset for every partition. """
    partitions = {}
    for t in taskset:
        if t.partition not in partitions:
            partitions[t.partition] = []
        partitions[t.partition].append(t)
    for p in partitions.itervalues():
        yield tasks.TaskSystem(p)

def all_partitions_are_schedulable(taskset):
    """ Check that all the partitions of the tasket are schedulable

    Uses the `blocked term` and computes a new response_time for each task
    """
    cpu_per_partition = 1
    for ts in iter_partitions_ts(taskset):
        if not fp.is_schedulable(cpu_per_partition, ts):
            return False
    return True

def has_new_response_times(taskset):
    """ Does any response_time differs from the previous_response_time? """
    for tsk in taskset:
        if tsk.previous_response_time != tsk.response_time:
            return True
    return False

def is_schedulable(taskset, lock=None):
    """ Test if the taskset is schedulable, considering lock overheads.

    The lock provided will be used to apply the bounds.
    Multiple bounds (with different spinlock types) are not supported.
    """
    if lock is None:
        lock = default_spinlock

    # Increase the cost and critical section durations
    charge_spinlock_overheads(taskset)

    # Initialize estimate and backup original costs
    for tsk in taskset:
        tsk.previous_response_time = None
        tsk.uninflated_cost = tsk.cost

    # Is it schedulable ? (considering `blocked` term)
    # Computes new `response_time`
    while all_partitions_are_schedulable(taskset):

        # Did we converge ?
        if not has_new_response_times(taskset):
            return True

        # Restore costs
        # And store new previous_response_time
        for tsk in taskset:
            tsk.cost = tsk.uninflated_cost
            tsk.previous_response_time = tsk.response_time

        # Uses the response_time to compute the blocked term
        # May change exec costs
        lock.apply_bounds(taskset)


    # Some partition is not schedulable anymore
    return False
