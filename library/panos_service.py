#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: panos_service
short_description: create a service object
description:
    - Create a service object. Service objects are fundamental representation of the applications given src/dst ports and protocol
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
    password:
        description:
            - password for authentication
        required: true
    username:
        description:
            - username for authentication
        required: false
        default: "admin"
    service_name:
        description:
            - name of the service
        required: true
    protocol:
        description:
            - protocol for the service, should be tcp or udp
        required: true
    port:
        description:
            - destination port
        required: true
    source_port:
        description:
            - source port
        required: false
        default: None
    commit:
        description:
            - commit if changed
        required: false
        default: true
'''

EXAMPLES = '''
# Creates service for port 22
  - name: create SSH service
    panos_service:
      ip_address: "192.168.1.1"
      password: "admin"
      service_name: "service-tcp-22"
      protocol: "tcp"
      port: "22"
'''

RETURN = '''
status:
    description: success status
    returned: success
    type: string
'''

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}


from ansible.module_utils.basic import AnsibleModule

try:
    import pan.xapi
    from pan.xapi import PanXapiError
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

_SERVICE_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
                 "/vsys/entry[@name='vsys1']" +\
                 "/service/entry[@name='%s']"


def service_exists(xapi, service_name):
    xapi.get(_SERVICE_XPATH % service_name)
    e = xapi.element_root.find('.//entry')
    if e is None:
        return False
    return True


def add_service(xapi, module, service_name, protocol, port, source_port):
    if service_exists(xapi, service_name):
        return False

    exml = ['<protocol>']
    exml.append('<%s>' % protocol)
    exml.append('<port>%s</port>' % port)
    if source_port:
        exml.append('<source-port>%s</source-port>' % source_port)
    exml.append('</%s>' % protocol)
    exml.append('</protocol>')

    exml = ''.join(exml)

    xapi.set(xpath=_SERVICE_XPATH % service_name, element=exml)

    return True


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        service_name=dict(required=True),
        protocol=dict(required=True, choices=['tcp', 'udp']),
        port=dict(required=True),
        source_port=dict(),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    if not ip_address:
        module.fail_json(msg="ip_address should be specified")
    password = module.params["password"]
    if not password:
        module.fail_json(msg="password is required")
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    service_name = module.params['service_name']
    if not service_name:
        module.fail_json(msg='service_name is required')
    protocol = module.params['protocol']
    if not protocol:
        module.fail_json(msg="protocol is required")
    port = module.params['port']
    if not port:
        module.fail_json(msg="port is required")
    source_port = module.params['source_port']
    commit = module.params['commit']

    try:
        changed = add_service(xapi, module,
                              service_name,
                              protocol,
                              port,
                              source_port)
        if changed and commit:
            xapi.commit(cmd="<commit></commit>", sync=True, interval=1)
    except PanXapiError as x:
        module.fail_json(msg=x.message)

    module.exit_json(changed=changed, msg="okey dokey")

if __name__ == '__main__':
    main()
