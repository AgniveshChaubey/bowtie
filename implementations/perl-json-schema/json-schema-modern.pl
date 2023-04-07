use strict;
use warnings;

use JSON::Schema::Modern;
use JSON::MaybeXS;

my $json = JSON::MaybeXS->new;
my $schema_validator = JSON::Schema::Modern->new;

my $jsonschema_version = $schema_validator->VERSION;

my %cmds = (
  start => sub {
    my ($request) = @_;
    die "Wrong version!" unless $request->{version} == 1;
    my $os_info = `uname -a`;
    my $lang_version = `perl -v | grep 'This is perl'`;
    $lang_version =~ s/.*v(\S+).*/$1/;

    return {
      ready => 1,
      version => 1,
      implementation => {
        language => 'perl',
        name => 'JSON-Schema-Modern',
        version => $jsonschema_version,
        homepage => 'https://metacpan.org/pod/JSON::Schema::Modern',
        issues => 'https://github.com/jhthorsen/json-schema-modern/issues',
        dialects => [
          'http://json-schema.org/draft-07/schema#',
          'http://json-schema.org/draft-06/schema#',
          'http://json-schema.org/draft-04/schema#',
        ],
        os => $os_info,
        language_version => $lang_version,
      },
    };
  },
  dialect => sub {
    my ($request) = @_;
    die "Not started!" unless $request->{started};
    return { ok => 0 };
  },
  run => sub {
    my ($request) = @_;
    die "Not started!" unless $request->{started};
    my $validator = $schema_validator->new($request->{case}->{schema});
    my @results;
    for my $test (@{$request->{case}->{tests}}) {
      push @results, { valid => $validator->validate($test->{instance}) };
    }
    return { seq => $request->{seq}, results => \@results };
  },
  stop => sub {
    die "Not started!" unless $_[0]->{started};
    exit 0;
  },
);

while (my $line = <STDIN>) {
  chomp $line;
  my $request = $json->decode($line);
  my $response = $cmds{$request->{cmd}}->($request);
  print $json->encode($response) . "\n";
}
