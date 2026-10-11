"""Same-host CPU actor launcher with native file-content read restrictions.

This is a frozen single-thread runtime, not a fresh VM or a hostile-code proof.
Metadata syscalls are not hidden; protected file contents are not readable.
"""
from pathlib import Path
import os
import signal
import sys
import time
from retry.qualify_pixel_package import PipeWorker


def sandbox_command(binary, clean, command):
    roots = [str(Path(clean).resolve()), str(Path(sys.prefix).resolve()),
             str(Path(sys.base_prefix).resolve()), '/usr/lib', '/usr/local/lib']
    return [str(binary), *roots, '--', *map(str, command)]


class SandboxWorker(PipeWorker):
    def __init__(self, command, directory, environment, *, sandbox):
        self.actor_pids = set()
        super().__init__(sandbox_command(sandbox, directory, command), directory, environment)
        try:
            os.set_blocking(self.process.stderr.fileno(),False)
            header=os.read(self.process.stderr.fileno(),4096).decode()
            self.actor_pids.update(int(line.split('=')[1]) for line in header.splitlines() if line.startswith('PIXEL_SANDBOX_ACTOR_PID='))
            self.check_memory()
            assert len(self.actor_pids) == 1
        except Exception:
            self.close()
            raise

    def check_memory(self):
        if not hasattr(self, 'process'):
            return
        path = Path('/proc') / str(self.process.pid)
        try:
            self.actor_pids.update(int(p) for p in (path/'task'/str(self.process.pid)/'children').read_text().split())
        except FileNotFoundError:
            pass
        for pid in self.actor_pids:
            try:
                for line in (Path('/proc')/str(pid)/'status').read_text().splitlines():
                    if line.startswith(('VmRSS:', 'VmHWM:')):
                        self.observed_peak_rss_bytes = max(self.observed_peak_rss_bytes, int(line.split()[1])*1024)
                    if line.startswith('Threads:'):
                        assert int(line.split()[1]) == 1
            except FileNotFoundError:
                pass
        if self.observed_peak_rss_bytes > self.memory_limit_bytes:
            raise MemoryError('Actor RSS limit')

    def close(self):
        if self.closed:
            return self.reap_receipt
        if self.process.poll() is None:
            self.process.send_signal(signal.SIGTERM)
            self.process.wait(timeout=2)
        result = super().close()
        result['actor_pids_absent'] = all(not (Path('/proc')/str(p)).exists() for p in self.actor_pids)
        result['actor_count'] = len(self.actor_pids)
        result['process_reaped'] &= result['actor_pids_absent']
        return result
