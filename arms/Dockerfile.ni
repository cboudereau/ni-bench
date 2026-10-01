# ni arm: native non-interactive build-time install (isolation-docker-compose ADR).
# Version pinning as for superpowers: image layer + build-log `plugin list`.
# NI_SOURCE selects the stage: marketplace (default, published pin) or local
# (the ADR's local-COPY fallback - an unpublished checkout staged into
# arms/ni-local/ by scripts/stage-ni-local.sh).
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

# local: COPY the staged HOME overlay that replicates byte-for-byte what the
# marketplace install writes (plugin cache dir, installed_plugins.json ledger,
# known_marketplaces.json, marketplace manifest, settings.json enabledPlugins).
# `plugin list` proves the CLI resolves it and logs the version at build time,
# exactly like the marketplace stage.
FROM ni-bench-base AS local
COPY --chown=node:node ni-local/home/ /opt/arm-home/
RUN HOME=/opt/arm-home claude plugin list

FROM ${NI_SOURCE}
# verbosity-policy ADR: entrypoint hook seeds terse level `full` into the throwaway HOME
COPY --chmod=755 ni-init.sh /opt/arm-init.d/ni-init.sh
