# Vessel

> Vessel is a service that watches your kubernetes resources and runs  several tools against them.

[![Docker Image](https://github.com/sourcesense/vessel/actions/workflows/tags.yaml/badge.svg)](https://github.com/sourcesense/vessel/actions/workflows/tags.yaml)

Vessel stores the results of tools that are run so that you can query them with a simple HTTP / json interface. 

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

## Operator

The official and supported way, go to [Vessel Operator](https://github.com/sourcesense/vessel-operator).

### Querying

The query interface is easy, you can pass in querystring the field you want to filter.  
The Model of the issue Vessel Collector stores is simple:

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

Retrieving issue of `deployment` and `job`:

```http
GET http://localhost:8089/query?kind=deployment&kind=job
```

Retrieving critical CVE:

```http
GET http://localhost:8089/query?issue=CRITICAL_CVE
```

## Development

Vessel is developed in python and built with poetry

```bash
git clone git@github.com:sourcesense/vessel.git
cd vessel
poetry install
```

### Run Vessel as a server

```bash
 poetry run vessel server --k8s-url $K8S_URL --k8s-token $K8S_TOKEN
```

### Run Vessel on a single resource

```bash
poetry run vessel single RESOURCE.yaml
```

## Roadmap

- Exit code implementation for CI integration
- Admission control for Kubernetes resources
- Unique web interface for all the Vessel resources
- Implement a scoring system
- Add grype tool
- Add kubelinter tool
- TLS support over Vessel service ingresses.

## Contributing

You are more than welcome to contribute adding new tools to vessel.

Take a look to the [contributing guidelines](CONTRIBUTING.md).
