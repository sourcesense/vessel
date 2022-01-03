import json 
import yaml
import logging
from ..models import Issue, Context
from ..manager import vessel_hook, vessel_result
from io import StringIO
from sh import kubesec, ErrorReturnCode

logger = logging.getLogger(__name__)

def resource_kubesec(k8s_object):
  result = StringIO()
  issues = []
  specyaml = yaml.dump(k8s_object)

  try:
    kubesec("scan", "-", _in=specyaml, _out=result)
  except BaseException:
    report = json.loads(result.getvalue())[0] # we examine one at the time always
    # todo: we use advise ?
    # for v in report['scoring'].get('advise', []):
    #   issues.append(Issue(name=f'{v["id"]}', metadata=v))
    for v in report['scoring'].get('critical', []):
      issues.append(Issue(name=f'{v["id"]}', metadata=v))
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
