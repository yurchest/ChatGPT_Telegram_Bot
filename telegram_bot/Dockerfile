# Use an official Python runtime as a parent image
FROM python:3.12.3-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (if needed for your bot’s webhooks or API server)
# EXPOSE 8080

# Command to run the bot
CMD ["python", "main.py"]