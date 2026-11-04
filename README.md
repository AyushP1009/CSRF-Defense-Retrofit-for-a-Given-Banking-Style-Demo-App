# CSRF Defense Retrofit — Banking-Style Demo App

ITIS 3200 group project: Samuel Lucas, Ayush Patel, Ian Wambua, Angel Urena.

## Goal
Demonstrate an intentionally vulnerable **fake-money** banking transfer endpoint that can be abused by a malicious cross-site form, then harden the app with a **synchronizer CSRF token** and **SameSite=Strict** session cookie.

> Educational local demonstration only. No real accounts, credentials, or financial transfers.

## Status
Project planning / implementation not yet started. **Check for TA-provided starter banking code before building a replacement.**

## Planned app features
- Login/logout with session-based authentication
- Fake account balances and transfer history
- POST /transfer (vulnerable baseline vs secured behavior)
- Local malicious-site auto-submit demo
- Automated checks for legitimate transfers, unauthorized transfers, and missing/invalid CSRF tokens
- Reset/seed script for reproducible defense

## Planned architecture
```
app/
  __init__.py
  auth.py
  banking.py
  csrf.py
  db.py
  templates/
    login.html
    dashboard.html
    transfer.html
  static/
    style.css
attacker/
  index.html
tests/
  test_banking.py
  test_csrf.py
docs/
  threat-model.md
  demo-script.md
requirements.txt
README.md
```
File layout may change when TA starter code is received.

## Security model
- Attacker controls a third-party page and can induce a logged-in victim to visit it.
- Attacker knows the transfer endpoint and form parameter names, but not the victim's secret token/session.
- Vulnerable bank checks session authentication only, allowing a forged transfer.
- Hardened bank requires a secret unpredictable synchronizer token on state-changing requests and validates it before processing them.
- SameSite=Strict reduces cross-site session-cookie attachment. Demonstrate **token enforcement separately** with cookie setting relaxed to show the explicit HTTP 403 response.
- Local testing of SameSite needs **different sites**, not just different ports on localhost. A cross-site setup can use distinct loopback hostnames as documented in the demo script.
- Protect sessions with HttpOnly, use Secure over HTTPS, and never deploy the deliberately vulnerable mode publicly.

## Project management
See [GitHub Issues](../../issues) for owners and acceptance criteria.

## Division of responsibilities
- **Samuel Lucas**: bank application and fake transaction workflow — Issue #1
- **Ayush Patel**: CSRF protection, cookie defense, integration — Issue #2
- **Ian Wambua**: cross-site attack page and security tests — Issue #3
- **Angel Urena**: report, README and presentation — Issue #4
- **Everyone**: final integration and defense rehearsal — Issue #5

## Development workflow
1. Clone this repository and create a branch per task, for example `feature/banking-app`.
2. Create small commits, push the branch, and open a pull request to `main`.
3. Have another member review each PR before merging.
4. Update this README with **real installation and run commands** once the starter implementation exists.
5. Capture reproducible demo evidence and document test account/transfer personalization from `(group registration order number) mod 14`.

## Deliverables
- Working vulnerable and secured demos, code in this public GitHub repository
- Approximately 5-page report (excluding references/AI appendix)
- 10-minute presentation and 2-minute Q&A

## Notes
The proposal's two IoT-related failure cases (HTTP sensor data interception and hardcoded firmware secrets) do not apply to this CSRF topic. The final project should focus on the unauthorized banking transfer and the concrete token/cookie defenses instead.
