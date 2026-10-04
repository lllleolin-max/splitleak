# Changelog

## 0.2.0

- Combine group, literal, subject, token and scoped-time candidate indices before
  complete pair evaluation. Preserve all relations, reason order/ratios,
  components, paths and repair/check behavior. The checker remains all-pairs.
- Avoid noncandidate Jaccard work on sparse inputs. Zero-threshold, dense and
  common-token cases retain quadratic work/output; indexing can increase memory
  and small-input latency. No input cap or exact-search bound changed.
- Emit ASCII-safe stdout/stderr machine JSON for arbitrary Unicode IDs under
  native/legacy Windows encodings. Saved UTF-8 JSON bytes and CLI exits remain
  compatible; source and existing outputs are protected.
- Add the installed SDK benchmark, 100 seeded 200-row all-pairs graph/workflow
  comparisons, encoding regression and documented before/after observations.
  Update both wheel names in the existing four-group CI matrix; retain the
  Windows/Python 3.14-only console-layout check and other groups' conditional
  skips. Remote CI/publication remain separate validation gates.

## 0.1.0

Original declared-relation graph, exact bounded repair and independent checker;
three real correction cycles and later console-runner layout correction remain
unchanged in the historical documentation and evidence.
