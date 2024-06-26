# Dockerfile for event_service
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Specify the command to run the application
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "event_service.wsgi:application"]

CMD ["python", "manage.py","runserver","0.0.0.0:8005"]

