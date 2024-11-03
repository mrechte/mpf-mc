"""RGB DMD on the RPi.

Contains support for the Raspi low-level RGB LED tile driver of hzeller
(https://github.com/hzeller/rpi-rgb-led-matrix).
"""
import atexit
import threading
import queue
import logging

from PIL import Image

from mpf.core.platform import RgbDmdPlatform
from mpf.platforms.interfaces.dmd_platform import DmdPlatformInterface

# the hzeller library (external dependency)
# pylint: disable-msg=ungrouped-imports
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
except ImportError:
    RGBMatrix = None
    RGBMatrixOptions = None


class RpiDmdPlatform(RgbDmdPlatform):

    """Raspberry Pi GPIO RGB DMD."""

    __slots__ = ["_dmd", "config"]

    def __init__(self, machine):
        """Initialize RGB DMD."""
        super().__init__(machine)
        if not RGBMatrix:
            raise AssertionError("Please install the rgbmatrix or RGB Matrix library to use a RGB Matrix on the RPi")

        self.features['tickless'] = True
        self._dmd = None
        self.config = None
        atexit.register(self.stop)

    async def initialize(self):
        """Initialize platform."""
        self.config = self.machine.config_validator.validate_config(
            config_spec='rpi_dmd',
            source=self.machine.config.get('rpi_dmd', {})
        )

    def stop(self):
        """Stop platform."""
        if self._dmd:
            self._dmd.stop()

    def __repr__(self):
        """Return string representation."""
        return '<Platform.RpiDmd>'

    def configure_rgb_dmd(self, name: str):
        """Configure rgb dmd."""
        if not self._dmd:
            self._dmd = RpiRgbDmdDevice(self.config)
        return self._dmd


class RpiRgbDmdDevice(threading.Thread):

    """A RpiRgbDmd device."""

    def __init__(self, mc, config, queue):
        """Initialize RpiRgbDmd device."""
        threading.Thread.__init__(self)
        if not RGBMatrix:
            raise AssertionError("Please install the rgbmatrix or RGB Matrix library to use a RGB Matrix on the RPi")
        self.log = logging.getLogger('MPF-MC RPI thread')
        self.mc = mc
        self.config = config
        self.queue = queue

    def run(self):
        # initialize Panel
        xs = self.config["cols"]
        ys = self.config["rows"]
        self.img = Image.frombytes("RGB", (xs, ys), b'\x11' * xs * ys * 3)
        self.rgb_opts = RGBMatrixOptions()
        # Rudeboy way of setting the RGBMatrixOptions
        for k, v in self.config.items():
            try:
                setattr(self.rgb_opts, k, v)
            except Exception:   # pylint: disable-msg=broad-except
                raise AssertionError("RpiRgbDmdDevice: couldn't set", k, v)
        self.matrix = RGBMatrix(options=self.rgb_opts)
        self.matrix.SetImage(self.img)
        # register exit fnction
        atexit.register(self.stop)
        # Loop on frame Queue
        while not self.mc.thread_stopper.is_set():
            try:
                frame = self.queue.get(block=True, timeout=1)
            except queue.Empty:
                if self.mc.thread_stopper.is_set():
                    self.log.info("Stopping DMD reading thread")
                    return
                else:
                    continue

            self.update(frame)
            

    def update(self, data):
        """Update DMD data."""
        self.img.frombytes(data)
        self.matrix.SetImage(self.img)

    def set_brightness(self, brightness: float):
        """Set brightness.

        Range is [0.0 ... 1.0].
        """
        self.matrix.brightness = brightness * 100

    def stop(self):
        """Stop device."""
        self.matrix.Clear()
