# Create Address Service

This stateless service, hidden from public endpoints, is a wrapper around the
Monero Wallet RPC to restrict the Ordering API's control over the actual wallet.

The Ordering API will have the following capabilities and ONLY the following
capabilities:

- Create new subaddresses
- See how much money a subaddress received
- See what transaction hashes are associated with a subaddress

