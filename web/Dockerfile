FROM python:2.7
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
EXPOSE 8080
ADD . /code
#CMD python app.py
CMD uwsgi uwsgi.ini
