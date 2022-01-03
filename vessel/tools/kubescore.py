import json 
import yaml
import logging
from ..models import Issue
from ..manager import vessel_hook, vessel_result
from io import StringIO
from sh import kube_score, ErrorReturnCode

logger = logging.getLogger(__name__)

def resource_kubescore(k8s_object):
  buf = StringIO()
  
  try:
      kube_score('score','-o','json', '-', _in=yaml.dump(k8s_object), _out=buf)
  except ErrorReturnCode:
      pass # We skip a bad returning code since kube score return bad code when it finds problems
  result = json.loads(buf.getvalue())[0] # take first always we just check one object at a time
  issues = [ Issue(name=v['check']['name'], metadata=v['comments']) for v in result['checks'] if v['grade'] <10 and not v['skipped']]
  
  return issues

@vessel_hook
def deployment(resource, ctx):
  return vessel_result(resource_kubescore(resource))

@vessel_hook
def deploymentconfig(resource, ctx):
  return vessel_result(resource_kubescore(resource))

@vessel_hook
def job(resource, ctx):
  return vessel_result(resource_kubescore(resource))

@vessel_hook
def statefulset(resource, ctx):
  return vessel_result(resource_kubescore(resource))

@vessel_hook
def daemonset(resource, ctx):
  return vessel_result(resource_kubescore(resource))
