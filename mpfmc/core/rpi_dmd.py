"""RGB DMD on the RPi.

Contains support for the Raspi low-level RGB LED tile driver of hzeller
(https://github.com/hzeller/rpi-rgb-led-matrix).
"""
import atexit
import threading
import queue
import logging
import socket
import os

# from PIL import Image

from mpf.core.platform import RgbDmdPlatform


class RpiRgbDmdDevice(threading.Thread):

    """A RpiRgbDmd device."""

    def __init__(self, mc, config, queue):
        """Initialize RpiRgbDmd device."""
        threading.Thread.__init__(self)
        self.log = logging.getLogger('MPF-MC RPI thread')
        self.mc = mc
        self.config = config
        self.queue = queue
        self.socket_path = self.config["dmd_socket"]
        self.frame_size = self.config["cols"] * self.config["rows"] * 3

        self.socket = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_DGRAM)


    def run(self):
        # register exit fnction
        atexit.register(self.stop)
        # initialize Panel prms
        # Initial Image
        data = b'\x11' * self.frame_size
        self.update(data)
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
        try:
            # '/tmp/dmd.socket'
            self.socket.sendto(data, self.socket_path)
        except FileNotFoundError:
            pass
            
    def set_brightness(self, brightness: float):
        """Set brightness.

        Range is [0.0 ... 1.0].
        """
        # TODO: This would require a more sophiscated UDP server
        # self.matrix.brightness = brightness * 100
        pass


    def stop(self):
        """Stop device."""
        # TODO reset default image
        data = b'\x00' * self.frame_size
        self.update(data)
        self.socket.close()

