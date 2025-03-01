#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (C) Copyright 2019-2022 Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "certified",
}

DOCUMENTATION = """
---
module: aoscx
version_added: "2.8.0"
short_description: Perform CLI operations in AOS-CX devices.
description: >
  This module provides management of CLI operations in AOS-CX devices.
author: Aruba Networks (ArubaNetworks)
"""

import json
import re
from itertools import chain

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.plugins.cliconf import CliconfBase, enable_mode

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (  # NOQA
    to_list,
    ComplexList,
)


class Cliconf(CliconfBase):
    """
    Cliconf class for AOS-CX

    This ArubaOSCX plugin provides CLI operations with ArubaOS-CX Devices
    """

    def __init__(self, *args, **kwargs):
        """
        init function
        """
        super(Cliconf, self).__init__(*args, **kwargs)

    @enable_mode
    def get_config(self, source="running", flags=None, format="text"):
        """
        Get the switch config
        """
        if source not in ("running", "startup"):
            return self.invalid_params(
                "fetching configuration from {0} is"
                " not supported".format(source)
            )
        if source == "running":
            cmd = "show running-config all"
        else:
            cmd = "show configuration"
        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, command):
        """
        Edit the switch config
        """
        for cmd in chain(["configure terminal"], to_list(command), ["end"]):
            self.send_command(cmd)

    def get(
        self,
        command,
        prompt=None,
        answer=None,
        sendonly=False,
        newline=True,
        check_all=False,
    ):
        """
        Get command output from switch
        """
        return self.send_command(
            command=command,
            prompt=prompt,
            answer=answer,
            sendonly=sendonly,
            newline=newline,
            check_all=check_all,
        )

    def get_device_info(self):
        """
        Get device info
        """
        device_info = {}

        device_info["network_os"] = "aruba"
        reply = self.get("show version")
        data = to_text(reply, errors="surrogate_or_strict").strip()

        match = re.search(r"Version (\S+)", data)
        if match:
            device_info["network_os_version"] = match.group(1)

        match = re.search(r"^MODEL: (\S+)\),", data, re.M)
        if match:
            device_info["network_os_model"] = match.group(1)

        reply = self.get("show hostname")
        data = to_text(reply, errors="surrogate_or_strict").strip()

        match = re.search(r"^Hostname is (.+)", data, re.M)
        if match:
            device_info["network_os_hostname"] = match.group(1)

        return device_info

    def get_capabilities(self):
        """
        Get capabilities
        """
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)

    def run_commands(self, commands=None, check_rc=False):
        """
        Run commands on the switch
        """
        if commands is None:
            raise ValueError("'commands' value is required")
        responses = list()
        for cmd in to_list(commands):

            if not isinstance(cmd, Mapping):
                cmd = {"command": cmd}

            try:
                out = self.send_command(**cmd)
            except AnsibleConnectionFailure as exception:

                if check_rc:
                    raise
                out = getattr(exception, "err", exception)

            out = to_text(out, errors="surrogate_or_strict")

            responses.append(out)

        return responses

    def set_cli_prompt_context(self):
        """
        Make sure we are in the operational cli mode
        :return: None
        """
        if self._connection.connected:
            self._update_cli_prompt_context(config_context=r"\(\S+\)#")
