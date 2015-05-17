FROM klokantech/supervisord

COPY . /usr/local/src/hawk/

RUN apt-get -qq update && apt-get -qq -y --no-install-recommends install \
    python-pip \
    uwsgi \
    uwsgi-plugin-python \
&& pip install -r /usr/local/src/hawk/requirements.txt

EXPOSE 5000

COPY supervisord.conf /etc/supervisord/
