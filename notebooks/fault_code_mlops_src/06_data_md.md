## Part 3 — Data strategy

### Manifest schema (one row per image)

| Field | Meaning |
|-------|---------|
| `path` | Image path |
| `code` | Ground-truth fault code |
| `class_idx` | Catalog index |
| `split` | train / val / test |
| `source` | `real` \| `synthetic` \| `seed` \| `augment` |
| `product_id` | Product context for closed-set intersection |

### Considerations

1. **Zero real photos today** → seeds + GAN for development only.
2. **Closed-set per product** → reject codes not on `HAS_ERROR_CODE`.
3. **PII** → claim photos may show homes/faces; retention + access control.
4. **Lineage** → never mix synthetic into historical claim analytics unflagged.
5. **Real hold-out** → frozen set for promotion; never train on it.
