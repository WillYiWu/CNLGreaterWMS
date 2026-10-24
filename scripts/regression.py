#!/usr/bin/env python3
"""Run all Django tests with an isolated database and no external network."""
import os
from pathlib import Path
import socket
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'greaterwms.test_settings'

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    with patch.object(socket.socket, 'connect', side_effect=AssertionError(
            'External network is disabled in regression tests; mock the integration.')):
        execute_from_command_line(['manage.py', 'test', '--noinput', '--verbosity=2'])
