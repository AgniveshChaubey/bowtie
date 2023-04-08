use strict;
use warnings;

use JSON::Schema::Modern;
use JSON qw( decode_json encode_json );

my $schema_version = JSON::Schema::Modern->VERSION;
my $started = 0;
my $validator;

my %cmds = (
  start => sub {
    my $args = shift;
    die "Wrong version!" unless $args->{version} == 1;
    $started = 1;
    my $dialects = [
      'https://json-schema.org/draft/2020-12/schema',
      'https://json-schema.org/draft/2019-09/schema',
      'http://json-schema.org/draft-07/schema#',
    ];
    return {
      ready => 1,
      version => 1,
      implementation => {
        language => 'perl',
        name => 'JSON::Schema::Modern',
        version => $schema_version,
        homepage => 'https://metacpan.org/pod/JSON::Schema::Modern',
        issues => 'https://github.com/karenetheridge/JSON-Schema-Modern/issues',
        dialects => $dialects,
      },
    };
  },
);

