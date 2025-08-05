# Use the official Python runtime image
FROM python:3.13-slim

# Create the app directory
RUN mkdir /app

# Set the working directory inside the container
WORKDIR /app

# Set environment variables 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 

RUN apt-get update && apt-get install -y netcat-openbsd

# Gunicorn Socket
RUN mkdir -p /run && chmod 777 /run

# Upgrade pip
RUN pip3 install --upgrade pip 

# Copy the Django project  and install dependencies
COPY require.txt  /app/

# run this command to install all dependencies 
RUN pip3 install --no-cache-dir -r require.txt

RUN playwright install --with-deps chromium

COPY entry.bash .
RUN chmod +x entry.bash

# Copy the Django project to the container
COPY . /app/

ENTRYPOINT ["./entry.bash"]