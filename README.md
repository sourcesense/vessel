# Vessel 


> Vessel is a service that watches your kubernetes resources and runs against them several tools.

[![Docker Image](https://github.com/sourcesense/vessel/actions/workflows/tags.yaml/badge.svg)](https://github.com/sourcesense/vessel/actions/workflows/tags.yaml)

It stores the results of runned tools so you can query them with a simple HTTP / json interface. 

#### Available tasks

- linter 
- [trivy](https://github.com/aquasecurity/trivy) 
- [kubesec](https://kubesec.io/)
- [kubescore](https://kube-score.com/)

## Usage

### Run with Docker (ephemeral storage)

Run:
```bash
docker run --rm -p 127.0.0.1:8089:8089/tcp --env K8S_URL=http://KUBERNETSURL --env K8S_TOKEN=TOKEN sourcesense/vessel:latest
```

### Helm

TBD

### Operator

TBD


### Quering
The query interface is easy, you can pass in querystring the field you want to filter.  
The Model of the issue that Vessel Collector stores is simple:

```
name:  name of the resource
namespace: namespace of the resource
kind: kind of the resource
issue: the issue 
issue_metadata: addintional metadata of the issue
tool: task that generated the issue
created_at: date of the issue
```

### Examples

Retrieves issue of `deplyment` and `job`:

```http
GET http://localhost:8089/query?kind=deployment&kind=job
```

Retrieves critical CVE:

```http
GET http://localhost:8089/query?issue=CRITICAL_CVE
```



## Development

Vessel collector is developed in python and built with poetry

```bash
git clone git@github.com:sourcesense/vessel.git
cd vessel
poetry install
```

### Run the collector

```bash
 poetry run vessel server --k8s-url K8S_URL --k8s-token K8S_TOKEN
```


### Run vessel on a single resource

```bash
poetry run vessel single RESOURCE.yaml
```

## Roadmap

- add kubelinter tool
- add grype tool
- implement a scoring system
- ci friendly exit codes based on the scoring
- implent as an admission control

## Contributing

You are more than welcome to coontribute new tools to vessel.  
Integration of a new tool is very simple:

- create a new python file/module inside `vessel.tools` module
- write a function with `@vessel_hook` annotation and name the function with the Kubernetes resource you want to handle
- you get passed a resource `dict` and a `vessel.models.Context`
- return an array of `vessel/models.Issue` with just `issue` and `issue_metadata` fields 
- wrap the array with `vessel_result` function
- You're done!!

NOTE that everything you need to operate your tools like command line utilities must eb installed in the docker container so add things accordingly to the Dockerfile.

See this [pull request]() as an example.

Make a single pull-request for every tool you want to add.