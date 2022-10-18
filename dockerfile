



FROM registry.redhat.io/openshift4/ose-jenkins-agent-base

COPY helm /usr/bin/helm  ---> untar helm-linux-amd64.tar.gz(Helm 3 CLI) to get helm client.
RUN chmod +x /usr/bin/helm
