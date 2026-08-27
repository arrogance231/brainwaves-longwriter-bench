# Security

Never place Hugging Face tokens, API keys, SSH material, or private story text in
the repository. Use environment variables or local key files. The server
launchers bind to localhost by default; add authentication and a reviewed
network policy before exposing an endpoint publicly. Report accidental secret
exposure privately to the repository maintainer and rotate the credential.
