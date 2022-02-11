FROM python:3.8
COPY . /app
# Create and change to the app directory.
WORKDIR /app
RUN pip install -r requirements.txt
 
# Service must listen to $PORT environment variable.

#CMD [ "python", "app.py" ]
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 app:app