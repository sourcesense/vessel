FROM python:3.9-alpine

WORKDIR /app
RUN mkdir /app/data

RUN apk add curl
RUN apk add --virtual mypacks build-base libffi-dev 
RUN pip install --upgrade pip
RUN pip install poetry

# install trivy

RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin 

COPY poetry.lock pyproject.toml /app/
RUN poetry install
RUN apk del mypacks

COPY tasks.json .
COPY exclusions.json .
COPY vessel_collector vessel_collector


EXPOSE 8089
ENTRYPOINT [ "poetry", "run", "vessel" ]
CMD ["server"]
