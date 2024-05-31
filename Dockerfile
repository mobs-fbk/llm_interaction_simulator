# Use the NVIDIA PyTorch image as the base image
FROM nvcr.io/nvidia/pytorch:24.05-py3

# Update the OS and install any necessary dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

# Install the ollama external service
RUN curl https://ollama.ai/install.sh | sh

# Create a user group and a user
ARG USER=mobs
ARG USER_ID=1008
ARG USER_GROUP=mobs
ARG USER_GROUP_ID=1008
RUN addgroup --gid ${USER_GROUP_ID} ${USER_GROUP}
RUN adduser --gecos "" --disabled-password --uid ${USER_ID} --gid ${USER_GROUP_ID} ${USER}
USER mobs

# Set environment variables
ENV OLLAMA_NUM_PARALLEL=4
ENV OLLAMA_MAX_LOADED_MODELS=4
ENV OLLAMA_MAX_QUEUE=4

# Copy the requirements.txt file and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the main.py file, project files, and the start script into the container
COPY main.py /app/
COPY src /app/src
COPY start.sh /app/

# Set the working directory
WORKDIR /app

# Make the start script executable
RUN chmod +x start.sh

# Set the entrypoint to the start script
ENTRYPOINT ["./start.sh"]
