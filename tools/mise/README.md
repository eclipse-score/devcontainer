<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# mise tool owners

These environment files are the single version owner for mise-provisioned
native and Python command line tools. `mise.native.lock` and
`mise.published.lock` are generated artifact metadata. Refresh them and the
legacy Bazel/Python compatibility outputs with:

```sh
tools/internal/mise/refresh.sh
```

The Python file intentionally has no mise dependency lock: each command is an
exact PyPI selection, and the ordinary Python facade continues to resolve its
normal dependencies through uv.
