# ni arm: native non-interactive build-time install (isolation-docker-compose ADR).
# Version pinning as for superpowers: image layer + build-log `plugin list`.
FROM ni-bench-base
# The marketplace declares ni with a github source, which the CLI clones over
# SSH; no SSH host key exists in the image, so rewrite to HTTPS for the build
# only, then drop the .gitconfig to keep arm HOMEs symmetric across arms.
RUN HOME=/opt/arm-home git config --global url.'https://github.com/'.insteadOf 'git@github.com:' \
 && HOME=/opt/arm-home git config --global --add url.'https://github.com/'.insteadOf 'ssh://git@github.com/' \
 && HOME=/opt/arm-home claude plugin marketplace add itsaspacestation/claude-marketplace \
 && HOME=/opt/arm-home claude plugin install ni@itsaspacestation \
 && HOME=/opt/arm-home claude plugin list \
 && rm /opt/arm-home/.gitconfig

# verbosity-policy ADR: entrypoint hook seeds terse level `full` into the throwaway HOME
COPY --chmod=755 ni-init.sh /opt/arm-init.d/ni-init.sh
