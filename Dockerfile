# Use the NVIDIA PyTorch image as the base image
FROM nvcr.io/nvidia/pytorch:22.02-py3

# Update the OS and install any necessary dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Add deadsnakes PPA to get Python 3.10
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-distutils python3.10-venv

# Update alternatives to set Python 3.10 as the default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Upgrade pip to the latest version
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py && rm get-pip.py

# Install the ollama external service
RUN curl https://ollama.ai/install.sh | sh

# Copy the requirements.txt file and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the main.py file and project files into the container
COPY main.py /app/
COPY src /app/src

# Set the working directory
WORKDIR /app

# Start a shell by default
CMD ["bash"]
