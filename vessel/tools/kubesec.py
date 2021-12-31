import json 
import yaml
import logging
from ..models import Issue, Context
from ..manager import vessel_hook, vessel_result
from io import StringIO
from sh import kubesec

logger = logging.getLogger(__name__)

def resource_kubesec(k8s_object):
  result = StringIO()
  issues = []
  yaml = yaml.dump(k8s_object)

  try:
    output = kubesec("scan", "-", _in=specyaml, _out=result)
  except BaseException:
    vulnerabilities = json.loads(result.getvalue())
    for v in vulnerabilities:
      issues.append(Issue(name=f'{v["object"]}', metadata=v["message"]))
  except ErrorReturnCode:
    logger.error("Unable to execute kubescan")
  
  return issues

@vessel_hook
def deployment(resource, ctx):
  return vessel_result(resource_kubesec(resource))

@vessel_hook
def deploymentconfig(resource, ctx):
  return vessel_result(resource_kubesec(resource))

@vessel_hook
def job(resource, ctx):
  return vessel_result(resource_kubesec(resource))

@vessel_hook
def statefulset(resource, ctx):
  return vessel_result(resource_kubesec(resource))

@vessel_hook
def daemonset(resource, ctx):
  return vessel_result(resource_kubesec(resource))
