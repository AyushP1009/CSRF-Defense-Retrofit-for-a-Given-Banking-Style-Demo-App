# Local CSRF Attack Demonstration (Ayush)


## Run the vulnerable baseline

From the repository root, in **Terminal 1**:

```bash
pip install -r requirements.txt
python database.py
python app.py
```

In the browser go to `http://localhost:5000/login`. Log in as `alice` with password `password123`. Confirm balance is $1,000. Leave this authenticated browser session active.

From the repository root, in **Terminal 2**:

```bash
python attacker/server.py
```

Using the **same browser profile**, visit `http://localhost:8000/index.html`. The page automatically submits the following HTML form into a hidden frame:

```html
<form action="http://localhost:5000/transfer" method="POST">
  <input type="hidden" name="receiver" value="attacker">
  <input type="hidden" name="amount" value="100">
</form>
```

Return to `http://localhost:5000/dashboard` and refresh. In the unprotected app, Alice's balance should be $900 and the attacker account should be $200, with a transfer recorded. The attacker site **cannot read the bank's response**; it only causes a request.

Reset fake data by stopping the bank and running `python database.py` again (while no process is writing the database), then restarting the bank. Test `http://localhost:8000/click-trigger.html` to demonstrate a different triggering action.

## Important SameSite details

`localhost:5000` and `localhost:8000` are **different origins but the same site** under the browser's SameSite rules. This setup is an effective baseline for demonstrating **CSRF token failure**, but it does **not** prove the effect of SameSite=Strict.

For the defense-in-depth cookie demonstration use separate local hostnames / sites, compatible with your browser, and coordinate with Ian on HTTPS, cookie `Secure`, host resolution, and exact security settings. Modern browsers often treat cookies without an explicit SameSite attribute as Lax, which can block cross-site POSTs before they reach token validation. Do not attribute such a failure to CSRF token checking. Do not modify the browser's security protections to force results.

