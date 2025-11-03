import asyncio, time
try:
    import gpiozero
except ImportError:
    gpiozero = None

class Speedometer:

    def __init__(self, gpio_a:int, gpio_b:int|None=None, pulses_per_rev:int=1, wheel_circ_m:float=1.0,
                 idle_timeout_s:float=2.0,
                 debounce_s: float=0.01):
        self.gpio_a = gpio_a
        self.gpio_b = gpio_b
        self.ppr = pulses_per_rev
        self.circ = wheel_circ_m
        self.idle_timout_s = idle_timeout_s
        self.debounce_s = debounce_s
        self._queue = asyncio.Queue(maxsize=1000)
        self._pi = None
        self._last_ns = None

        self._queue: asyncio.Queue[tuple] = asyncio.Queue(maxsize=1000)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._btn: gpiozero.Button | None = None
        self._last_ns: int | None = None
        self._idle_task: asyncio.Task | None = None
        self._pulse_event = asyncio.Event()  # signals “pulse happened”
        self._sent_zero = False  # prevents spamming zeros

    async def start(self):
        if gpiozero is None:
            raise RuntimeError("pigpio required for robust timing")

        self._btn = gpiozero.Button(self.gpio_a, pull_up=True, bounce_time=self.debounce_s)
        self._btn.when_pressed = self._cb

        # Background task to register zero:
        self._idle_task = asyncio.create_task(self._idle_zeroer())

    def _cb(self):
        # tick is in microseconds (wraps); use monotonic_ns for simplicity

        now = time.monotonic_ns()
        if self._last_ns is not None:
            dt = (now - self._last_ns) / 1e9
            rev_per_s = (1.0/dt)/self.ppr
            rpm = rev_per_s * 60
            #speed = rev_per_s * self.circ
            try: self._queue.put_nowait((now, rpm))
            except asyncio.QueueFull: pass

        self._last_ns = now
        self._sent_zero = False #  new activity, allow a future zero
        self._pulse_event.set()
        self._pulse_event.clear()

    async def _idle_zeroer(self) -> None:
        while True:
            try:
                await asyncio.wait_for(self._pulse_event.wait(), timeout=self.idle_timout_s)
                # a pulse happened; loop to wait again
                continue
            except asyncio.TimeoutError:
                if self._last_ns is not None and not self._sent_zero:
                    try:
                        self._queue.put_nowait((time.monotonic_ns(),0.0))
                    except asyncio.QueueFull:
                        pass
                self._sent_zero=True


    async def read(self):
        return await self._queue.get()

    async def stop(self):
        if self._pi: self._pi.stop()
