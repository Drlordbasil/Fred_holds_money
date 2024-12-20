# Known Issues and Solutions

## 1. **Credits Deduction and Synchronization**
### Issue:
- Credits are deducted both in the frontend and backend, leading to double deductions or inconsistencies.
### Solution:
- The frontend no longer deducts credits locally. Instead, it fetches the updated balance from the backend after each attempt.

---

## 2. **Session Expiry**
### Issue:
- If a session expires while a user is logged in, the frontend might behave as though the user is still logged in.
### Solution:
- Added a periodic check with the `/session` endpoint to validate the session state. If the session is invalid, the user is logged out and redirected.

---

## 3. **Payment Creation Errors**
### Issue:
- PayPal payments may fail to create due to invalid data or server errors.
### Solution:
- Added detailed logging and descriptive error messages for failed payments. Users are informed of the issue and prompted to try again.

---

## 4. **Handling Empty Inputs**
### Issue:
- Empty prompts or missing required fields could cause errors during API calls.
### Solution:
- Backend now validates all inputs and returns clear error messages if inputs are missing or invalid.

---

## 5. **Concurrent Updates**
### Issue:
- Credits and pot amounts may get out of sync when multiple tabs or devices are used simultaneously.
### Solution:
- The backend is now the single source of truth for all state updates. Frontend fetches updated states after every action.

---

## 6. **Error Handling During LLM Attempts**
### Issue:
- If an error occurs during the handling of a prompt (e.g., tool execution fails), the user receives a generic error message.
### Solution:
- Improved error handling and logging to ensure errors are logged and user-friendly messages are displayed.

---

## 7. **Cashout Limitations**
### Issue:
- Users could attempt cashouts with insufficient balances.
### Solution:
- Cashout requests are validated thoroughly in the backend. Insufficient balance errors are returned before processing begins.
