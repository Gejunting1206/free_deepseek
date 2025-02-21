FROM python:3.9-slim-buster

WORKDIR /app

# Install Chrome and Chromedriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4

# Download and install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install ./google-chrome-stable_current_amd64.deb -y

# Download and install ChromeDriver (Make sure to use the correct version for your Chrome version)
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/121.0.6167.85/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip -d /opt/
RUN mv /opt/chromedriver /usr/local/bin/chromedriver
RUN chown root:root /usr/local/bin/chromedriver
RUN chmod +x /usr/local/bin/chromedriver

# Set environment variables for Chrome and ChromeDriver
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_DRIVER=/usr/local/bin/chromedriver

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD Xvfb :99 -screen 0 1280x720x24 & uvicorn main:app --host 0.0.0.0 --port 8000
