import asyncio, time
try:
    import pigpio
except ImportError:
    pigpio = None

class Speedometer:

    def __init__(self, gpio_a:int, gpio_b:int|None=None, pulses_per_rev:int=20, wheel_circ_m:float=1.0):
        self.gpio_a = gpio_a
        self.gpio_b = gpio_b
        self.ppr = pulses_per_rev; self.circ = wheel_circ_m
        self._queue = asyncio.Queue(maxsize=1000)
        self._pi = None
        self._last_ns = None

    async def start(self):
        if pigpio is None:
            raise RuntimeError("pigpio required for robust timing")

        self._pi = pigpio.pi()

        self._pi.set_mode(self.gpio_a, pigpio.INPUT)
        self._pi.set_pull_up_down(23, pigpio)
        self._pi.set_glitch_filter(GPIO_A, 3000) # microseconds
        self._pi.callback(self.gpio_a, pigpio.RISING_EDGE, self._cb)

    def _cb(self, gpio, level, tick):
        # tick is in microseconds (wraps); use monotonic_ns for simplicity

        now = time.monotonic_ns()
        if self._last_ns is not None:
            dt = (now - self._last_ns) / 1e9
            rev_per_s = (1.0/dt)/self.ppr
            speed = rev_per_s * self.circ
            try: self._queue.put_nowait((now, speed))
            except asyncio.QueueFull: pass

        self._last_ns = now

    async def read(self):
        return await self._queue.get()

    async def stop(self):
        if self._pi: self._pi.stop()
