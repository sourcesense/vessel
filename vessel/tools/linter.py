import re
from ..manager import vessel_hook

# Monkey Password in env interceptor
def look_like_password(env): 
  detected = [] 
  if env:
    for var in env:
      pwd_pattern = '^.*password|pass|pwd|credential.*$'
      ref_pattern = '^.*ref|name.*$'
      if re.search(pwd_pattern, var['name'].lower()) and not re.search(ref_pattern, var['name'].lower()):
        if var.value:
          detected.append({ "name": var['name'], "value_from": "plain text" })
  return detected

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

        if container.readinessProbe is None:
          missing.append('readiness_probe')

      else:
        if container.get('livenessProbe', None) is None:
          missing.append('liveness_probe')

        if container.get('readiness_probe', None) is None:
          missing.append('readiness_probe')
    
    if container['resources'].get('limits') is None:
        missing.append('limits')
  
    if container['resources'].get('requests') is None:
        missing.append('requests')

    if container.get('security_context') is None:
      missing.append('security_context')

    detetect_look_like_password = look_like_password(container['env'])
    
    if len(detetect_look_like_password) > 0:
      data['look_like_password'] = detetect_look_like_password

  for miss in missing:
    data['name'] = name
    data['namespace'] = k8s_object['metadata']['namespace']
    data['issue'] = f"missing_{miss}"

    detected.append(data)

  return missing


@vessel_hook
def deployment(resource):
  return container_inspec(resource)
  