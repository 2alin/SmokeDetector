# Standby mode

## What is standby mode?

SmokeDectector can be ran in standby mode as a backup copy just in case the main Smokey breaks down.
While in Standby mode, SmokeDetector will not make reports in chat, send posts to Metasmoke or listen
to commands (except `!!/failover` and `!!/stappit`).

Standby mode can be deactivated by running the `!!/failover` command. This will make the backup 
instance begin to run like the standard SmokeDetector.
