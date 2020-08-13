# put any third-party Python dependencies you need for your job here
# you do not need to list the apache-beam package - it is already installed
# with klio-exec (in the Dockerfile)
# be sure to hard-pin the versions, i.e.:
# foo-package==1.2.3
{%- if not klio.use_fnapi %}
# The Dataflow worker needs access to the exact environment/dependencies as the
# job had when it was launched, so we include the `klio-exec` (that
# is used to actually launch the job) to be installed as well.
klio-exec
{%- endif %}