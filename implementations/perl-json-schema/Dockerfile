FROM perl:5.32

WORKDIR /app

RUN cpanm JSON
RUN cpanm JSON::Schema::Modern

COPY json-schema-modern.pl .

CMD ["perl", "json-schema-modern.pl"]
