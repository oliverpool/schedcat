from schedcat.locking.model import Unordered
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


def save_costs(taskset):
    """ Save the task cost into another attribute """
    for t in taskset:
        t.saved_cost = t.cost

def restore_costs(taskset):
    """ Restore the task cost from another attribute """
    for t in taskset:
        t.cost = t.saved_cost


def init_response_time(taskset):
    """ Initialize the 'previous_response_time' """
    for t in taskset:
        t.previous_response_time = t.response_time

def update_response_time(taskset):
    """ Update the 'previous_response_time'
    Return True if at least one response_time has been changed
    """
    updated = False
    for t in taskset:
        if t.previous_response_time != t.response_time:
            t.previous_response_time = t.response_time
            updated = True
    return updated


def stable_schedule(ts, cpus, lock=default_spinlock, max_iteration=1000, is_schedulable=fp.is_schedulable):
    """ Try to converge to a stable schedule for the taskset (considering locking bounds)

    Multiple bounds (with different spinlock types) is not supported yet.
    The lock provided will be used to apply the bounds.
    """
    taskset = ts.copy()
    save_costs(taskset)
    init_response_time(taskset)

    iteration = 0
    fixed_point_reached = False
    while not fixed_point_reached:

        # restore and update costs
        restore_costs(taskset)
        lock.apply_bounds(taskset)

        # compute and update response_time
        if not is_schedulable(cpus, taskset):
            break
        fixed_point_reached = not update_response_time(taskset)

        # next iteration
        iteration += 1
        if iteration > max_iteration:
            raise Exception("MaxIteration reached")

    return fixed_point_reached, taskset
