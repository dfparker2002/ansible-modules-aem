#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Lean Delivery Team <team@lean-delivery.com>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

__version__ = '1.0.0'

DOCUMENTATION = '''
---
module: aem_packmgr
short_description: Manage AEM packages
description:
  - Manage AEM packages
'''

import requests
import xml.etree.ElementTree as ET

def _pgk_exist(url, login, password, pkg_name):
    response = requests.get(url+'/crx/packmgr/service.jsp?cmd=ls', auth=(login, password))
    aem_response = ET.fromstring(response.text)

    packages_list = []
    for package in aem_response.findall('response/data/packages/package/name'):
        packages_list.append(package.text)

    download_names = []
    for elements in aem_response.findall('response/data/packages/package/downloadName'):
        download_names.append(elements.text)

    if any(pkg_name in x for x in (packages_list, download_names)):
        print('installed')
        return True
    else:
        print('not installed')
        return False
    pass

def _pkg_install(url, login, password, file_name, file_path, install=False, force=True):
    files = {'file':  (file_name, open(file_path, 'rb'), 'application/zip')}
    values = {'install': install, 'force': force}
    response = requests.post(url+'/crx/packmgr/service.jsp', files=files, data=values, auth=(login, password))
    aem_response = ET.fromstring(response.text)
    if (aem_response.find("response/status").attrib['code']) == '200':
        pkg_name = aem_response.find("response/data/package/name").text
        install_status = requests.get(url+'/crx/packmgr/service.jsp?cmd=inst&name='+pkg_name, auth=(login, password))
        aem_inst_response = ET.fromstring(install_status.text)
        if (aem_inst_response.find("response/status").attrib['code']) == '200':
            print('ok')
            return True
        else:
            print(json.dumps({
                "failed" : True,
                "msg"    : install_status.text
            }))
            _pkg_remove(url, login, password, pkg_name)
            return False
    else:
        print(json.dumps({
            "failed" : True,
            "msg"    : response.text
        }))
        return False
    pass

def _pkg_remove(url, login, password, pkg_name):
    response = requests.get(url+'/crx/packmgr/service.jsp?cmd=rm&name='+pkg_name, auth=(login, password))
    aem_response = ET.fromstring(response.text)
    if (aem_response.find("response/status").attrib['code']) == '200':
        print('ok')
        return True
    else:
        print('fail')
        return False
    pass

def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            pkg_name=dict(type='str'),
            pkg_path=dict(type='str'),
            aem_user=dict(required=True, type='str'),
            aem_passwd=dict(required=True, type='str', no_log=True),
            aem_url=dict(required=True, type='str'),
            aem_force=dict(default='false', type='bool')
        ),
        supports_check_mode=False
    )

    state = module.params.get('state')
    aem_user = module.params.get('aem_user')
    aem_passwd = module.params.get('aem_passwd')
    aem_url = module.params.get('aem_url')
    aem_force=module.params.get('aem_force')
    state_changed = False
    message = "no changes"
    if state in ['present', 'install']:
        pkg_name = module.params.get('pkg_name')
        if aem_force or not _pgk_exist(aem_url, aem_user, aem_passwd, pkg_name):
            pkg_path = module.params.get('pkg_path')
            if _pkg_install(aem_url, aem_user, aem_passwd, pkg_name, pkg_path):
                state_changed = True
                message = "Installation package " + pkg_name + " was successful"
                pass
            else:
                message = "Installation package " + pkg_name + " is failed"
                module.fail_json(msg=message)
            pass
        else:
            pass
        pass
    elif state in ['absent']:
        if _pgk_exist(aem_url, aem_user, aem_passwd, pkg_name):
            pkg_name = module.params.get('pkg_name')
            if _pkg_remove(aem_url, aem_user, aem_passwd, pkg_name):
                state_changed = True
                message = "Removing package " + pkg_name + " was successful"
            else:
                message = "Removing package " + pkg_name + " is failed"
                module.fail_json(msg=message)
        pass

    module.exit_json(changed=state_changed, msg=message)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()