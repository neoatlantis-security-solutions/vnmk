Volatile Non-Memorable Key System
=================================

The Volatile Non-Memorable Key(VNMK) system, is a system designed at releasing
a user's password, or part of it, via Internet.

The system releases a user's password or cryptographical key, in such a way:

1. The user must request, via HTTPS, for a session. This is done by visiting a
special URL. **This session has a time-out, within which the user MUST
authenticate itself, otherwise the server will destroy user's credentials.**

2. The user logs himself in via several OpenID providers, and provide a 6-digit
code. The server checks for OpenID authentication and the 6-digit code. If both
are valid, the password is released. Otherwise, the server destroys user's
credential.
