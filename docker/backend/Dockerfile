FROM python:3.11-slim

COPY ../.. /app
COPY ../../api /app/api
COPY ../../requirements.txt /app/api/requirements.txt
WORKDIR /app

ENV TEMP /tmp
RUN mkdir -p $TEMP


#RUN apt-get update && apt-get install -y \
#    ffmpeg \
#    build-essential \
#    libssl-dev \
#    libffi-dev \
#    python3-dev \
#    libxml2-dev \
#    libxslt1-dev

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "manage.py", "runserver"]