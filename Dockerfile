ARG PYTHON_VERSION=3.10.14
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

# Copy the source code into the container.
COPY . .

# Install your application
RUN pip install -e .

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
CMD python main.py
