# Phone OTP Refactor - Replace Email OTP

## Status: In Progress

### Steps:
- [x] Step 1: Create PHONE_OTP_TODO.md ✅
- [ ] Step 2: Read dependent templates (login.html, dashboard.html)
- [ ] Step 3: Edit app.py - DB schema add phone, signup/verify logic for phone, remove mail.
- [ ] Step 4: Edit templates/signup.html - add phone field, JS update.
- [ ] Step 5: Update other templates if email shown.
- [ ] Step 6: Stop server, delete database/retail.db, re-run app.py
- [ ] Step 7: Test signup with phone OTP (console print)

**Simulate SMS:** Console print "SMS to phone: OTP xxx"

**Real SMS:** Ask for Twilio SID/Auth Token/phone later.

