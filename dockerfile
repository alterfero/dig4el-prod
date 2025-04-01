# Use an official Python image
FROM python:3.10

# Set the working directory
WORKDIR /usr/src/app

# Copy the requirements file
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose Streamlit’s default port
EXPOSE 8501

# Default command (can be overridden in docker-compose)
CMD ["python", "main.py"]