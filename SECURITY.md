# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest (main) | ✅ |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **security@example.com** with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

You will receive an acknowledgement within 48 hours and a resolution timeline within 7 days.

## Security Best Practices

- Rotate all secrets in `.env` before deployment; never use defaults in production.
- Enable TLS on all external endpoints.
- Restrict database ports to the internal Docker network.
- Keep all base Docker images up to date.
- Run the weekly security scan workflow (`.github/workflows/security-scan.yml`).
- Review CodeQL and Trivy alerts promptly.

## Disclosure Policy

We follow responsible disclosure. Once a fix is released, we will publish a security advisory crediting the reporter (unless anonymity is requested).
