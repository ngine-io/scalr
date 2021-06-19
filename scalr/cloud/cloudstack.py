import os
import base64

from scalr.cloud import ScalrBase
from scalr.log import log

from cs import CloudStack


class CloudstackScalr(ScalrBase):

    def __init__(self):
        super().__init__()
        self.cs = CloudStack(
            endpoint=os.getenv('CLOUDSTACK_API_ENDPOINT'),
            key=os.getenv('CLOUDSTACK_API_KEY'),
            secret=os.getenv('CLOUDSTACK_API_SECRET'),
        )

    def get_current(self) -> list:
        if self.current_servers is None:
            servers = self.cs.listVirtualMachines(
                tags=[{
                    'key': 'scalr',
                    'value': self.name,
                }],
                fetch_list=True,
            )
            self.current_servers = sorted(servers, key = lambda i: i['created'])
        return self.current_servers

    def ensure_running(self):
        for server in self.get_current():
            log.info(f"server {server['name']} status {server['state']}")
            if server['state'] in ['stopping', 'stopped']:
                if not self.dry_run:
                    self.cs.startVirtualMachine(id=server['id'])
                    log.info(f"Server {server['name']} started")
                else:
                    log.info(f"Dry run server {server['name']} started")

    def _get_service_offering(self, name):
        res = self.cs.listServiceOfferings(name=name)
        if not res:
            raise Exception(f"Error: Service offering not found: {name}")
        return res['serviceoffering'][0]

    def _get_zone(self, name):
        res = self.cs.listZones(name=name)
        if not res:
            raise Exception(f"Error: Zone not found: {name}")
        return res['zone'][0]

    def _get_template(self, name):
        for tf  in ['community', 'self']:
            res = self.cs.listTemplates(name=name, templatefilter=tf)
            if res:
                break
        else:
            raise Exception(f"Error: Template not found: {name}")
        return res['template'][0]

    def _get_deploy_params(self, lc):
        user_data =  lc.get('user_data')
        if user_data:
            user_data = base64.b64encode(user_data.encode("utf-8"))

        return {
            'serviceofferingid': self._get_service_offering(name=lc['service_offering']).get('id'),
            'affinitygroupnames': lc.get('affinity_groups'),
            'securitygroupnames': lc.get('security_groups'),
            'templateid': self._get_template(name=lc['template']).get('id'),
            'zoneid': self._get_zone(name=lc['zone']).get('id'),
            'userdata': user_data,
            'keypair': lc.get('ssh_key'),
            'group': lc.get('group'),
            'rootdisksize': lc.get('root_disk_size'),
        }

    def scale_up(self, diff: int):
        log.info(f"scaling up {diff}")

        if diff > 0:
            lc = self.launch_config.copy()
            params = self._get_deploy_params(lc)

        while diff > 0:

            name = self.get_unique_name()
            params.update({
                'name': name,
            })
            lc_tags = lc.get('tags', {})
            tags = [{
                'key': "scalr",
                'value': self.name,
            }]
            for key, value in lc_tags.items():
                if key != self.name:
                    tags.append({
                        'key': key,
                        'value': value
                })

            if not self.dry_run:
                server = self.cs.deployVirtualMachine(**params)
                self.cs.createTags(
                    resourceids=[server['id'],],
                    resourcetype="UserVm",
                    tags=tags,
                )
                log.info(f"Creating server name={name}")
            else:
                log.info(f"Dry run creating server name={name}")
            diff -= 1

    def scale_down(self, diff: int):
        log.info(f"scaling down {diff}")
        while diff > 0:
            server = self.get_selected_server()
            if not self.dry_run:
                self.cs.destroyVirtualMachine(id=server['id'])
                log.info(f"Deleting server id={server['id']}")
            else:
                log.info(f"Dry run deleting server id={server['id']}")
            diff -= 1
