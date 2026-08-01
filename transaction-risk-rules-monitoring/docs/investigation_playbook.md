# Investigation Playbook - Transaction Risk Alerts

Period: Feb 2025 - Apr 2025  
Project: Transaction Risk Rules & Alert Monitoring

## Purpose

Turn automated alerts into clear risk decisions while protecting legitimate merchants and users.

## Triage buckets

1. **P1-investigate** (high severity)
   - Immediate analyst ownership
   - Check linked velocity, device, and merchant signals
   - Freeze only when evidence supports fraud

2. **P2-review** (medium severity)
   - Queue review within SLA
   - Confirm whether threshold noise or true anomaly

## Rule playbooks

### R_VEL_01 - User velocity burst
- Evidence: many transactions / high amount sum in a short window
- Checks: user history, device consistency, geo/channel shift
- Decision: allow / step-up auth / block

### R_DEV_01 - Shared device anomaly
- Evidence: one device linked to many users or burst activity
- Checks: device age, account linkage, prior fraud on device
- Decision: allow / challenge / block network

### R_MER_01 - Merchant spike anomaly
- Evidence: sudden txn count or amount spike vs merchant baseline
- Checks: settlement pattern, chargeback history, campaign events
- Decision: monitor / hold settlement / escalate compliance

## End-to-end rule change validation

1. Propose threshold change
2. Run baseline vs candidate on full payment logs
3. Compare false-positive rate, precision, alert volume
4. Confirm legitimate pass-through remains high
5. Register durable control version in `risk_rules`
6. Document decision in validation log

## Ownership principle

Make the call with imperfect information, record evidence, and own the outcome.
