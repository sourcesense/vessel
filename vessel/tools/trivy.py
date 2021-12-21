from ..models import Issue, Context
from ..manager import vessel_hook, vessel_result
from sh import trivy
import json 

def get_images(resource):
  return [e['image'] for e in  resource['spec']['template']['spec']['containers']]


def run_image(resource, ctx:Context):
  images = get_images(resource)
  issues = []
  for img in images:
    inner_registry = img.split('/')[0]
    registry = ctx.registries.get(inner_registry)
    if registry:
      _env = {
        'TRIVY_USERNAME': registry['user'],
        'TRIVY_PASSWORD': registry['password'],
      }
      img = img.replace(inner_registry, registry['host'])
    else:
      _env = {}
    try:
      out = trivy("-q", "image", "-s", "HIGH,CRITICAL", "-f", "json", img, _env=_env)
    except Exception:
      print(f"error with trivy for image {img}")
      continue
    json_out = json.loads(out.stdout)
    if json_out.get("Results"):
      for r in json_out["Results"]:
        if r.get("Vulnerabilities"):
          for v in r["Vulnerabilities"]:
            issues.append(Issue(name=f'{v["Severity"]}_CVE', metadata={
                "id": v["VulnerabilityID"],
                "severity": v["Severity"],
                "package": v["PkgName"],
                "name": v.get("Title", ""),
                "description": v["Description"],
                "link": v["PrimaryURL"],
              }))
  return vessel_result(issues)
 

@vessel_hook
def deployment(resource, ctx):
  return run_image(resource, ctx)

@vessel_hook
def deploymentconfig(resource, ctx):
  return run_image(resource, ctx)

@vessel_hook
def job(resource, ctx):
  return run_image(resource, ctx)

@vessel_hook
def statefulset(resource, ctx):
  return run_image(resource, ctx)

@vessel_hook
def daemonset(resource, ctx):
  return run_image(resource, ctx)

