# ni arm: native non-interactive build-time install (isolation-docker-compose ADR).
# Version pinning as for superpowers: image layer + build-log `plugin list`.
# NI_SOURCE selects the stage: marketplace (default, the latest published
# release) or local (an unpublished checkout staged into arms/ni-local/ by
# scripts/stage-ni-local.sh when NI_LOCAL_SRC is set).
ARG NI_SOURCE=marketplace

FROM ni-bench-base AS marketplace
# The marketplace declares ni with a github source, which the CLI clones over
# SSH; no SSH host key exists in the image, so rewrite to HTTPS for the build
# only, then drop the .gitconfig to keep arm HOMEs symmetric across arms.
RUN HOME=/opt/arm-home git config --global url.'https://github.com/'.insteadOf 'git@github.com:' \
 && HOME=/opt/arm-home git config --global --add url.'https://github.com/'.insteadOf 'ssh://git@github.com/' \
 && HOME=/opt/arm-home claude plugin marketplace add itsaspacestation/claude-marketplace \
 && HOME=/opt/arm-home claude plugin install ni@itsaspacestation \
 && HOME=/opt/arm-home claude plugin list \
 && rm /opt/arm-home/.gitconfig

# local: the staged marketplace is added from its path inside the image, so
# the install writes the same ledger entries (ni@itsaspacestation) as the
# published path; `plugin list` logs the +local.<sha> version at build time.
FROM ni-bench-base AS local
COPY --chown=node:node ni-local/ /opt/ni-local/
RUN HOME=/opt/arm-home claude plugin marketplace add /opt/ni-local \
 && HOME=/opt/arm-home claude plugin install ni@itsaspacestation \
 && HOME=/opt/arm-home claude plugin list

FROM ${NI_SOURCE}
# verbosity-policy ADR: entrypoint hook seeds terse level `full` into the throwaway HOME
COPY --chmod=755 ni-init.sh /opt/arm-init.d/ni-init.sh
