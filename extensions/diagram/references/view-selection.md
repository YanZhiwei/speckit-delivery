# View selection

Choose one view. A second view is a separate request, because mixing views
produces a diagram that answers nothing precisely.

## before-after

Use when the change moves an owner, a boundary, a public contract, or a data
path. Show only the parts that move; unchanged context is one node labelled
with its owner.

```mermaid
flowchart LR
  subgraph before[Before]
    A[Router] --> B[Inline validation]
  end
  subgraph after[After]
    C[Router] --> D[Validation service]
  end
  classDef changed fill:#ffe8a3,stroke:#b8860b
  class D changed
```

## call-path

Use when the sequence of components for one request changes. Start at the entry
point and stop at the durable boundary, not at every helper.

```mermaid
flowchart LR
  U[Client] --> G[Gateway]
  G --> S[Service]
  S --> R[(Repository)]
```

## impact

Use when the risk is who else depends on the change. Group dependents by
contract, not by directory.

```mermaid
flowchart TD
  C[Changed contract] --> A[Adapter A]
  C --> B[Adapter B]
  C --> T[Test suite]
```

## sequence

Use when ordering, retries, or failure handling across actors is the point.

```mermaid
sequenceDiagram
  participant C as Client
  participant S as Service
  participant Q as Queue
  C->>S: request
  S->>Q: enqueue
  Q-->>S: ack
  S-->>C: accepted
```

## Size limits

- `max_nodes` and `max_edges` come from the project configuration.
- Prefer one view at a lower level of detail over a wide diagram.
- If the honest answer needs more nodes, split by boundary and link the parts;
  do not shrink the labels until they stop meaning anything.
