FROM alpine:latest

RUN apk add --no-cache perl perl-utils
RUN apk add --no-cache build-base

RUN cpan JSON::MaybeXS
RUN cpan JSON::Schema::Modern

COPY json-schema-modern.pl /

CMD ["perl", "/json-schema-modern.pl"]