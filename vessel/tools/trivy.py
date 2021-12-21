from ..models import Issue
from ..manager import vessel_hook, vessel_result
from sh import trivy
import json 

def get_images(resource):
  return [e['image'] for e in  resource['spec']['template']['spec']['containers']]


def run_image(resource):
  images = get_images(resource)
  issues = []
  for img in images:
    try:
      out = trivy("-q", "image", "-s", "HIGH,CRITICAL", "-f", "json", img)
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
  return issues
 

@vessel_hook
def deployment(resource):
  return vessel_result(run_image(resource))

@vessel_hook
def deploymentconfig(resource):
  return vessel_result(run_image(resource))

@vessel_hook
def job(resource):
  return vessel_result(run_image(resource))

@vessel_hook
def statefulset(resource):
  return vessel_result(run_image(resource))

@vessel_hook
def daemonset(resource):
  return vessel_result(run_image(resource))

