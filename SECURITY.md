# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please send a detailed report to the repository maintainers via
GitHub's private vulnerability reporting feature:

1. Go to the **Security** tab of this repository
2. Click **Report a vulnerability**
3. Provide a detailed description of the vulnerability

## What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix or mitigation**: As soon as practical

## Supported Versions

Only the latest released version receives security updates.

## Security Best Practices

When using this collection:
- Always use `validate_certs: true` (the default) in production
- Store credentials in Ansible Vault or an external secrets manager
- Use `no_log: true` for tasks that handle sensitive data
- Review role defaults before deploying to production
