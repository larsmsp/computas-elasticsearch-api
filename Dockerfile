FROM p0bailey/docker-flask
MAINTAINER Lars Martin S. Pedersen <lmp@computas.com>

COPY app /var/www/app
RUN pip install -r /var/www/app/requirements.txt