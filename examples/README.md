# Registration schema example

Copy to the data_collect directory root:

```bash
cp examples/registration.yaml schema.yaml
```

This schema collects student registration fields via webhook JSON keys (`email`, `linux_username`, `name`, etc.) and exports a CSV with Chinese headers.

After submissions are collected, the full export is written to `data/export.csv`. Import that file into any downstream system that accepts CSV input.
