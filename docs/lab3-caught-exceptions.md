# Caught operational errors in Lab 3

`oceens.posthog_telemetry.capture_exception(error)` reports a caught failure using
this process's explicitly initialized client. Startup binds it, shutdown clears it,
and an unconfigured process reports nothing. Capture failures do not replace the
existing response, rollback, fallback or daemon continuation.

The call remains inside the existing PostHog request or survey context: web errors
inherit the signed-in email; daemon errors inherit `oceens-summaries` and `survey_id`.
No client is created at import time, and the SDK global client is not used.

## Covered failures

There are 35 explicit capture points:

| Area | Capture points | Existing outcome retained |
|---|---:|---|
| Student routes | 2 | Rollback and JSON error |
| Survey routes | 3 | Existing JSON error |
| Summary routes | 2 | Existing conflict/server error |
| Prompt routes | 3 | Existing redirect/JSON error |
| Section/question routes | 6 | Rollback and JSON error |
| Survey template routes | 5 | Existing JSON error |
| User routes | 1 | Existing JSON error |
| Provider tests | 6 | Existing configuration/network/unexpected-error response |
| Survey deletion service | 1 | Existing rollback and return |
| Persisted exchange-rate setting | 1 | Existing default fallback |
| Web daemon shutdown timeout | 1 | Existing forced termination |
| Summaries daemon | 4 | Existing failed-summary status and continuation |

The inventory excludes expected validation/control flow: invalid optional IDs,
invalid form amounts, nonnumeric NPS answers, missing-key badges, optional dates,
non-JSON provider-error bodies, optional encoding repair, and CSV dialect fallback.
The standalone XLSX loader is not part of either deployed process and does not
initialize telemetry. Error results returned without a raised exception are outside
this inventory of caught exceptions.

## Validation

The tests exercise opt-out, lifecycle cleanup, capture-failure isolation and actual
SDK context propagation for web email and daemon survey identity. SDK events are
dropped before send; tests require no real token or external service. Local HTTP
compatibility checks also verify that an unhandled exception retains its HTTP 500,
body and content type when PostHog is disabled. A personal exception observed on
staging remains a separate lab proof.
