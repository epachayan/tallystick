# Interaction-protocol specifications (generated)

Generated from `specs/*.toml` by `make spec-doc`. Do not edit by hand: `make check` fails if this file differs from the specifications. The prose account is in [README.md](README.md).

## bearer3

bearer tokens and self-written logs; no counterparty signatures. Roles P, I, E; objects G, S, X, R.

| # | message | from | to | signed | binds | forwards | requires | receiver checks |
|---|---|---|---|---|---|---|---|---|
| 1 | `grant` | P | I | no | - | - | - | - |
| 2 | `subgrant` | I | E | no | - | - | grant | - |
| 3 | `exec_receipt` | E | I | no | - | - | subgrant | - |
| 4 | `report` | I | P | no | - | - | exec_receipt | - |

## hop3

per-hop bilateral commitment; intermediary re-signs. Roles P, I, E; objects G, S, X, R.

| # | message | from | to | signed | binds | forwards | requires | receiver checks |
|---|---|---|---|---|---|---|---|---|
| 1 | `grant` | P | I | yes | G | - | - | - |
| 2 | `grant_ack` | I | P | yes | G | - | grant | - |
| 3 | `subgrant` | I | E | yes | S | - | grant | - |
| 4 | `subgrant_ack` | E | I | yes | S | - | subgrant | - |
| 5 | `exec_receipt` | E | I | yes | X | - | subgrant_ack | - |
| 6 | `report` | I | P | yes | R | - | exec_receipt | - |
| 7 | `report_ack` | P | I | yes | R | - | report | - |

## chain3

witness-carrying delegation; intermediary forwards, never restates. Roles P, I, E; objects G, S, X, R.

| # | message | from | to | signed | binds | forwards | requires | receiver checks |
|---|---|---|---|---|---|---|---|---|
| 1 | `grant` | P | I | yes | G | - | - | - |
| 2 | `grant_ack` | I | P | yes | G | - | grant | - |
| 3 | `subgrant` | I | E | yes | S, G | grant | grant | subset:S:G |
| 4 | `subgrant_ack` | E | I | yes | S, G | - | subgrant | - |
| 5 | `exec_receipt` | E | I | yes | X, S | - | subgrant_ack | - |
| 6 | `report` | I | P | yes | R | subgrant_ack, exec_receipt | exec_receipt | equal:R:X |
| 7 | `report_ack` | P | I | yes | R | - | report | - |
