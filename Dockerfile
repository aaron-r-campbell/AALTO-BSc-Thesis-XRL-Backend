FROM selenium/standalone-chrome

USER root

# Set the working directory to /app
WORKDIR /app

# Copy the application code into the container at /app
COPY . .

# Create the images directory
RUN mkdir images

# Setup python and pip
RUN apt-get update && apt-get install python3-distutils -y
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Define the command to run the Flask app when the container starts
CMD ["python3", "app.py"]
