FROM python:3.12-slim

WORKDIR /app

# Copy and install dependencies first to speed up future builds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your bot's code
COPY . .

# Run your bot script (change main.py if your file is named index.py or bot.py)
CMD ["python", "src_py/bot.py"]
