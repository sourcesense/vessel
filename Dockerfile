FROM python:3.9-alpine

WORKDIR /app
RUN mkdir /app/data

RUN apk add curl
RUN apk add --virtual mypacks build-base libffi-dev 
RUN pip install --upgrade pip
RUN pip install poetry

# install trivy

RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin 

# install kubesec

RUN cd /tmp && \
    curl -sfL -o kubesec_linux_amd64.tar.gz https://github.com/controlplaneio/kubesec/releases/download/v2.11.4/kubesec_linux_amd64.tar.gz && \
    cd /usr/local/bin && \
    tar -xzvf /tmp/kubesec_linux_amd64.tar.gz kubesec && \
    rm /tmp/kubesec_linux_amd64.tar.gz

# Install Kubescore

RUN cd /tmp && \
    curl -sfL -o kube-score.tar.gz https://github.com/zegl/kube-score/releases/download/v1.13.0/kube-score_1.13.0_linux_amd64.tar.gz && \
    cd /usr/local/bin && \
    tar -xzvf /tmp/kube-score.tar.gz kube-score && \
    rm /tmp/kube-score.tar.gz

COPY poetry.lock pyproject.toml /app/
RUN poetry install
RUN apk del mypacks

COPY vessel vessel

EXPOSE 8089
ENTRYPOINT [ "poetry", "run", "vessel" ]
CMD ["server"]
