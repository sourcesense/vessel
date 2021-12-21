import re
from .. import Issue
from .. import vessel_hook, vessel_result


def container_inspec(k8s_object):
  
  detected = []

  containers = k8s_object['spec']['template']['spec']['containers']
  data = {}
  missing = []
  spec = k8s_object['spec']

  if hasattr(spec, 'replicas') and spec['replicas'] == 1:
    missing.append('multiple_replicas')

  for container in containers:
    name = k8s_object['metadata']['name']
      
    if not k8s_object['kind'] == 'JobList':
      if k8s_object['kind'] == 'DeploymentConfig':

        if container.get('livenessProbe', None) is None:
          missing.append('liveness_probe')

        if container.get('readinessProbe') is None:
          missing.append('readiness_probe')

      else:
        if container.get('livenessProbe', None) is None:
          missing.append('liveness_probe')

        if container.get('readinessProbe', None) is None:
          missing.append('readiness_probe')
    
    if container['resources'].get('limits') is None:
        missing.append('limits')
  
    if container['resources'].get('requests') is None:
        missing.append('requests')

    if container.get('security_context') is None:
      missing.append('security_context')

    
    if container.get('env'):
      for var in container.get('env'):
        pwd_pattern = '^.*password|pass|pwd|credential.*$'
        ref_pattern = '^.*ref|name.*$'
        if re.search(pwd_pattern, var['name'].lower()) and not re.search(ref_pattern, var['name'].lower()):
          if var.get('value'):
            detected.append(Issue(name="looks_like_password", metadata={ "name": var['name'], "value_from": "plain text" }))

    
  
  for miss in missing:
    detected.append(Issue(name=f"missing_{miss}"))

  return detected


@vessel_hook
def deployment(resource):
  return vessel_result(container_inspec(resource))

@vessel_hook
def deploymentconfig(resource):
  return vessel_result(container_inspec(resource))

@vessel_hook
def job(resource):
  return vessel_result(container_inspec(resource))

@vessel_hook
def statefulset(resource):
  return vessel_result(container_inspec(resource))

@vessel_hook
def daemonset(resource):
  return vessel_result(container_inspec(resource))