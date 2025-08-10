FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY data_generator.py .

# Run the data generator
CMD ["python", "data_generator.py"]