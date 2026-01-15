## 2024-05-23 - [SSRF Protection in URL Extraction]
**Vulnerability:** The URL extraction feature allowed users to input any URL, which was then fetched by the server without validation. This could allow attackers to access internal services (localhost, private networks, cloud metadata) via Server-Side Request Forgery (SSRF).
**Learning:** Libraries like `trafilatura` or `requests` do not have built-in SSRF protection. Validating the scheme (http/https) is insufficient because it doesn't prevent access to internal IPs or domains resolving to them.
**Prevention:** Implement a strict validation layer that:
1.  Resolves the DNS hostname to an IP address.
2.  Checks if the IP is global (not private, loopback, or link-local).
3.  Rejects requests to disallowed IPs.
Note: A robust solution should also handle DNS rebinding (TOCTOU) by validating the IP at the connection level, but pre-validation significantly reduces the attack surface.

## 2026-01-15 - [Insecure Anonymous Session Management]
**Vulnerability:** Anonymous user sessions were generated solely based on the User-Agent header using `hashlib.sha256(user_agent)`. This caused all users with the same browser configuration (e.g., corporate environments, same browser version) to share the same session and data.
**Learning:** Relying on `User-Agent` (or even IP + UA) for session identification is insecure due to high collision rates. Client-side generated unique IDs or server-side cookies are necessary.
**Prevention:** Implemented a hybrid approach:
1. Frontend generates a unique UUID (v4) and stores it in localStorage.
2. Frontend sends this UUID in `X-Anonymous-ID` header.
3. Backend prioritizes `X-Anonymous-ID` for session generation, falling back to User-Agent only for legacy clients.
