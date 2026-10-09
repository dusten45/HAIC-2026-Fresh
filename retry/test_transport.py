"""Behavioral checks for the trusted local evaluator's bounded pipe transport."""

import sys
import time
import unittest

import numpy as np

from retry.process_probe import Participant


class TransportTests(unittest.TestCase):
    def worker(self, response_code):
        code = (
            'import sys,time\n'
            'print(\'{"ready":true,"simulator_imported":false}\',flush=True)\n'
            'sys.stdin.readline()\n' + response_code
        )
        return Participant(sys.executable, command_override=[sys.executable, "-u", "-c", code])

    def test_partial_response_without_newline_times_out_and_reaps(self):
        child = self.worker('sys.stdout.write(\'{"action":\');sys.stdout.flush();time.sleep(5)\n')
        try:
            started = time.monotonic()
            with self.assertRaises(TimeoutError):
                child.call("act", np.zeros((4, 84, 84), dtype=np.float32), timeout=0.15)
            self.assertLess(time.monotonic() - started, 0.75)
            self.assertIsNotNone(child.process.poll())
        finally:
            child.close()

    def test_oversized_response_is_bounded_and_reaped(self):
        child = self.worker('sys.stdout.write("x"*(1024*1024+65536));sys.stdout.flush();time.sleep(5)\n')
        try:
            with self.assertRaisesRegex(RuntimeError, "bounded protocol size"):
                child.call("act", np.zeros((4, 84, 84), dtype=np.float32))
            self.assertIsNotNone(child.process.poll())
        finally:
            child.close()

    def test_fragmented_valid_response_is_assembled(self):
        child = self.worker(
            'sys.stdout.write(\'{"action":[0,\');sys.stdout.flush();time.sleep(.01)\n'
            'sys.stdout.write(\'0.1,0]}\\n\');sys.stdout.flush();time.sleep(.1)\n'
        )
        try:
            response, _ = child.call("act", np.zeros((4, 84, 84), dtype=np.float32))
            self.assertEqual(response["action"], [0, 0.1, 0])
        finally:
            child.close()


if __name__ == "__main__":
    unittest.main()
