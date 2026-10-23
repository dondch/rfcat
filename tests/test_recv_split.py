"""A message that arrives in two USB reads must still be delivered.

runEP5_recv() parses recv_queue in a `while (msglen >= 5)` loop. Before the fix, when the
queue held the start of a message but not all of it, the loop re-read the same queue and
spun forever without returning to the USB read, so the rest never arrived and recv() timed out.
"""
import struct
import unittest

from rflib.const import *
from rflib.fakedongle_nic import FakeRfCat
from rflib.chipcon_usb import ChipconUsbTimeoutException


class TestSplitMessage(unittest.TestCase):
    def test_message_split_across_two_reads_is_delivered(self):
        d = FakeRfCat()
        payload = bytes(range(256)) * 2  # 512 byte NIC_RECV message, as a large packet produces
        message = b"@" + struct.pack("<BBH", APP_NIC, NIC_RECV, len(payload)) + payload
        chunks = [message[:192], message[192:]]

        def read_ep5(timeout=100):
            if chunks:
                return chunks.pop(0)
            raise usb.USBError("Operation timed out (FakeDongle)")

        d._recvEP5 = read_ep5
        try:
            got, _ = d.recv(APP_NIC, NIC_RECV, wait=3000)
        except ChipconUsbTimeoutException:
            self.fail("recv() timed out: the receive loop never fetched the rest of the message")
        self.assertEqual(got, payload)


if __name__ == "__main__":
    unittest.main()
