# What the marketplace accepts

A listing is instructions that run with somebody else's keys. These rules are
what a moderator checks; `tools/check.py` checks everything a machine can.

## Every listing

1. **It does what its summary says.** The summary is the outcome, in one sentence.
2. **It carries nothing of yours.** No keys, no emails, no account IDs, no
   private addresses. Your specifics become blanks (projects) or are removed (roles).
3. **It declares what it needs.** Every key a prompt reads and every data source
   it calls is in `needs`, with a label a stranger understands and a link to get one.
4. **A key is optional only if the prompt says what happens without it.**
5. **It asks for no more than the work needs.** A role that only writes does not
   get `bash`. A data source lists only the tools the work calls.
6. **The prompt is readable.** No hidden text, encodings, or instructions aimed at
   anything but the job: nothing that tells an agent to send data elsewhere, to
   ignore yaaf's rules, or to fetch and run code that is not in the listing.

## Roles

- Generic: a role serves many projects, so it has no blanks and names no customer.
- One job. If it needs two very different prompts, it is two roles.

## Projects

- Every blank has a question a stranger can answer and an example that is not yours.
- It passes the $0 fire drill with the examples filled in.
- A receipt, if attached, is the one yaaf produced. Do not edit it.

## Updates

Every version is reviewed; the review card shows only what changed. An update
that adds a tool or a key needs two approvals, and installs must re-consent.

## Refused

Malware, credential collection, deception about what a listing does, listings
that impersonate another publisher, spam and near-duplicates of your own listing.

## Reports and appeals

Use the Report link on any listing page, which opens an issue. A moderator
replies on the issue. To appeal a removal, open an issue with the listing id.
