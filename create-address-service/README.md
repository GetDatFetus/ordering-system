# Create Address Service

This stateless service is a wrapper around the Monero Wallet RPC to aid in
isolation and wallet securely.

It ensures that the Ordering API has the following capabilities and ONLY the
following capabilities:

- Create new subaddresses
- See how much money a subaddress received
- See what transaction hashes are associated with a subaddress

Its endpoints are NOT exposed to the public.

