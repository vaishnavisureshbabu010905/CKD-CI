## Summary
This PR upgrades the CKD-CI clinical application with production-oriented analytics, model governance, and safer observability support.

## Changes included

### Dashboard
- Added Prediction History page enhancements
  - date filter
  - predicted class filter
  - model version filter
  - pagination
  - latest-first sorting
  - CSV export
- Added Admin Analytics summary page
- Made Streamlit/joblib imports lazy or optional for test stability

### API
- Added model registry endpoints
- Included predictions router so `/predictions/history` is exposed on the API app
- Improved prediction history DB access to safely handle missing tables

### Logging and observability
- Added structured logging
- Added request ID tracking
- Added rotating log files
- Added PHI-safe sanitized prediction logging
- Added in-memory metrics endpoint

### Reliability
- Updated test support objects for authz/history cases
- Verified all tests pass

## Why this matters
These changes move CKD-CI closer to an industry-style clinical AI system by improving:
- traceability
- admin visibility
- model governance
- operational safety
- usability for clinicians and admins

## Validation
- Ran full test suite
- All tests passed

## Next recommended work
- add server-side filtering/pagination for prediction history API
- connect Streamlit analytics to a real DB-backed integration test setup
- finalize auth/role checks for every admin-facing workflow if any remain
