FROM python:3.11

RUN apt-get update && apt-get install -y wget gnupg lsb-release curl && apt-get clean all && \
    wget -O- https://apt.releases.hashicorp.com/gpg |  gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt update && apt install -y terraform && \
    apt-get clean all

RUN curl -LO "https://github.com/GoogleCloudPlatform/terraformer/releases/download/$(curl -s https://api.github.com/repos/GoogleCloudPlatform/terraformer/releases/latest | grep tag_name | cut -d '"' -f 4)/terraformer-datadog-linux-$(dpkg --print-architecture)" && \
    chmod +x terraformer-datadog-linux-$(dpkg --print-architecture) && \
    mv terraformer-datadog-linux-$(dpkg --print-architecture) /usr/local/bin/terraformer

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY conf.yaml execute.sh conf_example.yaml ./