import bounds

class Spinlock(object):
    def __init__(self, total_overhead=0, critical_overhead=0, apply_lp_bounds_function=None):
        if not apply_lp_bounds_function:
            apply_lp_bounds_function = bounds.apply_pfp_lp_unordered_bounds
        self._apply_lp_bounds = apply_lp_bounds_function
        self.total_overhead = total_overhead
        self.critical_overhead = critical_overhead

    def apply_bounds(self, ts):
        """Apply LP bounds"""
        self._apply_lp_bounds(ts)


class Unordered(Spinlock):
    def __init__(self, total_overhead=0, critical_overhead=0):
        super(Unordered, self).__init__(
            total_overhead,
            critical_overhead,
            bounds.apply_pfp_lp_unordered_bounds,
        )

class Fifo(Spinlock):
    def __init__(self, total_overhead=0, critical_overhead=0):
        super(Fifo, self).__init__(
            total_overhead,
            critical_overhead,
            bounds.apply_pfp_lp_msrp_bounds,
        )

class Priority_Unordered(Spinlock):
    def __init__(self, total_overhead=0, critical_overhead=0):
        super(Priority_Unordered, self).__init__(
            total_overhead,
            critical_overhead,
            bounds.apply_pfp_lp_prio_bounds,
        )

class Priority_Fifo(Spinlock):
    def __init__(self, total_overhead=0, critical_overhead=0):
        super(Priority_Fifo, self).__init__(
            total_overhead,
            critical_overhead,
            bounds.apply_pfp_lp_prio_fifo_bounds,
        )
