FROM python:3.9-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
	apt-get install -y gcc libpq-dev python3-venv python3.9-venv && \
	rm -rf /var/lib/apt/lists/*

# RUN apt-get upgrade python-virtualenv     

# Copy project files (including requirements.txt)
COPY . /app/

# Set up venv and debug venv bin directory
RUN python3 -m venv /app/.venv && ls -l /app/.venv/bin/

# Download spacy model and run migrations
RUN /app/.venv/bin/python3 -m spacy download en_core_web_sm && \
	/app/.venv/bin/python3 manage.py makemigrations && \
	/app/.venv/bin/python3 manage.py migrate

# Expose port 9000
EXPOSE 9000

# Start Django server
CMD ["/app/.venv/bin/python3", "manage.py", "runserver", "0.0.0.0:9000"]
