# MQTT Discovery implementation plan

Approved design: the user requested the previously discussed MQTT implementation.
Use the existing dedicated checkout on branch `codex/mqtt-discovery`.

The app publishes active rules as MQTT sensors grouped into one device. An opt-in
switch enables publishing. Supervisor service discovery supplies broker credentials;
manual broker settings are available. No Home Assistant configuration file is needed.
Stable per-installation IDs survive restarts. Retained configuration, QoS 1, birth
subscription, LWT and reconnect resynchronization cover HA/broker/app restarts.
States retain the existing German text, with next_date and days_until attributes.
The configurable timezone defaults to Europe/Berlin. Disabled/deleted rules have
their retained discovery/state topics removed. Credentials never appear in HTTP
responses, read-only feeds, or error messages. Existing REST users can opt in safely.

- [x] Add failing tests for dates, validation/redaction, discovery lifecycle,
  reconnect, removal and broker unavailability.
- [x] Implement MQTT settings, supervisor discovery and background publisher.
- [x] Add GUI controls, status, dependency lock, version 0.2.0 and documentation.
- [x] Run unit suite, browser check and code review; fix material findings.
- [x] Publish version, update installed app, enable discovery and verify four sensors.
- [x] Back up configuration/dashboard, migrate consumers, remove the marked REST
  block and reload REST; verify states and dashboard without a Core restart.
