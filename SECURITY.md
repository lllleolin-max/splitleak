# Security and reporting

Never submit sensitive dataset rows in public issues. Send a synthetic reproduction with fresh opaque IDs, declared policy and observed behavior. Open a public issue for non-sensitive correctness problems; private reporting channel is not established. There is no claim of security certification or identity verification.

Input text remains local, but stable IDs, component paths, spans and source commitments can be identifying. Hashes do not anonymize content or prevent dictionary attacks. Review all outputs before sharing. A valid check means only the declared relation policy is satisfied; it does not certify complete ML leakage detection or fairness. Preserve the source and inspect a proposed assignment before joining it to training data.

CLI refuses overwrite; outputs are proposals and assignment manifests, not source mutations. This is a local trusted-file tool, not an OS sandbox or adversarial multi-tenant service. Apply/check recompute relations rather than trusting a cached witness or a claimed valid flag. INFEASIBLE and UNKNOWN must never be translated into "safe dataset" by a wrapper.
