# Contributing to Vessel

## Choosing a tool

Everything that produces an output can be used inside Vessel to gather information and do scans.

## Integrating the tool

Integration of a new tool is a very simple three stage process:

- **Stage 1**
  - Add the tool inside the Vessel container, by adding it into the `Dockerfile`.
- **Stage 2**
  - Create a new python file inside `vessel/tools` directory named after the tool you want to add and populate it with as many functions as the Kubernetes you want to handle, declaring for each one a `@vessel_hook` annotation.
  - Inside the module you will get passed a resource `dict` and a `vessel.models.Context` and will need to return an array of `vessel/models.Issue` with just `issue` and `issue_metadata` fields.
  - The array of `vessel/models.Issue` will need to be wrapped with the`vessel_result` function.
- **Stage 3**
  - Add your tool (or not) to the defaults.

## A practical example

Here's an example of the workflow used to integrate [kubesec](https://kubesec.io/) tool.

### Stage 1:  make the tool available inside the container

It's easy to add a tool to the container, by adding a section like this to the [Dockerfile](https://github.com/sourcesense/vessel/blob/main/Dockerfile#L15-L21):

```dockerfile
# install kubesec

RUN cd /tmp && \
    curl -sfL -o kubesec_linux_amd64.tar.gz https://github.com/controlplaneio/kubesec/releases/download/v2.11.4/kubesec_linux_amd64.tar.gz && \
    cd /usr/local/bin && \
    tar -xzvf /tmp/kubesec_linux_amd64.tar.gz kubesec && \
    rm /tmp/kubesec_linux_amd64.tar.gz
```

### Stage 2: create the module file

Have a look at the file named [`kubesec.py`](https://github.com/sourcesense/vessel/blob/main/vessel/tools/kubesec.py) under the `vessel/tools` path. [The import section](https://github.com/sourcesense/vessel/blob/main/vessel/tools/kubesec.py#L1-L7) is structured to include all the needed modules. In this case we will have:

```python
import json 
import yaml
import logging
from ..models import Issue, Context
from ..manager import vessel_hook, vessel_result
from io import StringIO
from sh import kubesec, ErrorReturnCode_2
```

Pay attention to the `from` lines, you'll need to import `Issue` and `Context` functions from `..models` (the `vessel/models.py` file) and `vessel_hook` and `vessel_result` from `..manager` (the `vessel/manager.py` file) to be able to properly uniform the output of the command.

The last statement `from sh import kubesec, ErrorReturnCode_2` uses the `sh` Python module to make `kubesec` usable as a function and declares its return code `ErrorReturnCode_2`, since `kubesec` returns **2** if it finds critical problems with the passed resource.

Next [we activate the logger](https://github.com/sourcesense/vessel/blob/main/vessel/tools/kubesec.py#L9), like this:

```python
logger = logging.getLogger(__name__)
```

And then we have [the crucial part](https://github.com/sourcesense/vessel/blob/main/vessel/tools/kubesec.py#L11-L28) of the module, the execution of the `kubesec` tool. 

The `kubesec` command executes as we would launch this from a terminal:

```console
$ cat myresource.yaml | kubesec scan -
```

The typical output of a problematic yaml will be something like this:

```json
[
  {
    "object": "Pod/calico-node-qqdmj.kube-system",
    "valid": true,
    "fileName": "STDIN",
    "message": "Failed with a score of -35 points",
    "score": -35,
    "scoring": {
      "critical": [
        {
          "id": "Privileged",
          "selector": "containers[] .securityContext .privileged == true",
          "reason": "Privileged containers can allow almost completely unrestricted host access",
          "points": -30
        },
        {
          "id": "HostNetwork",
          "selector": ".spec .hostNetwork == true",
          "reason": "Sharing the host's network namespace permits processes in the pod to communicate with processes bound to the host's loopback adapter",
          "points": -9
        }
      ],
      "passed": [
       ...
      ],
      "advise": [
       ...
      ]
    }
  }
]
```

This means we need to cycle over the `[ { "scoring": { "critical": [] } } ]` section of the json, extracting for each problem the `id` as a unique identifier and the entire critical record for metadata.

This translates in this code snippet:

```python
def resource_kubesec(k8s_object):
  result = StringIO()
  issues = []
  specyaml = yaml.dump(k8s_object)

  try:
    kubesec("scan", "-", _in=specyaml, _out=result)
  except ErrorReturnCode_2:
    report = json.loads(result.getvalue())[0]
    for v in report['scoring'].get('critical', []):
      issues.append(Issue(name=f'{v["id"]}', metadata=v))
  except BaseException:
    logger.error("Unable to execute kubescan")

  return issues
```

We are declaring three main variables:

1. `result` to get the entire buffer of the output coming from the `kubesec` command;

2. `issues` to contain all the issues in an array;

3. `specyaml` in which we dump the yaml content of the resource we're handling;

We execute `kubesec` and if it fails with return code 2 (so the yaml is considered problematic) we load the `[0]` record of the json into the `report` variable and we cycle over all the `critical` records under `scoring`.

After this, we'll have the result of the scan in `issues`, ready to be returned to Vessel.

[Last section](https://github.com/sourcesense/vessel/blob/main/vessel/tools/kubesec.py#L30-L48) will include, for each resource you'll want to handle, a function named after the resource introduced by a `@vessel_hook` annotation:

```python
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
```

### Stage 3: make the tool part (or not) of the defaults

The new tool could become a default or not, depending on how the `vessel/cli.py` is configured.

If you want it to become a default there are two sections you'll need to change, related to the one shot mode:

```python
@cli.command()
@click.argument('resource', type=click.File())
@click.option('-t', '--tools', envvar='TASKS', default="linter,trivy,kubesec,kubescore", type=click.STRING, help="Tools to run separated by commas [default]")
```

And the server mode:

```python
@cli.command()
@click.option('-n', '--namespaces', envvar='NAMESPACES', default=None, type=click.STRING, help="Namespaces to watch separated by commas [default]")
@click.option('-t', '--tools', envvar='TOOLS', default="linter,trivy,kubesec,kubescore", type=click.STRING, help="Tools to run separated by commas [linter,trivy,kubesec]")
```

## General recommendations

Once everything described in this page is in place, you can make a single pull-request for every tool you want to add.
