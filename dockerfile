FROM python:3.10.9-slim as base_image

ENV PIP_DISABLE_PIP_VERSION_CHECK=on

RUN pip install --upgrade pip
WORKDIR /tmp
COPY requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /opt
COPY . .
EXPOSE 8000
ENTRYPOINT ["bash", "entrypoint.sh"]

FROM base_image as prod_image
CMD ["gunicorn", "todolist.wsgi", "-w", "2", "-b", "0.0.0.0:8000"]

FROM base_image as dev_image
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
