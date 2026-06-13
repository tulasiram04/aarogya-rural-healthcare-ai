# Demo Flow

This guide walks through a complete end-to-end demo of **AAROGYA**, from initial patient interaction on low-bandwidth Telegram bot client to clinical monitoring on the Next.js medical dashboard.

### Step 1: Login Dashboard
- Navigate to `http://localhost:3000/login`
- Enter credentials:
  - **Phone**: `9876543200`
  - **Password**: `admin123`
- Click **Log In** to access the Doctor/Healthcare Worker control center.

### Step 2: Open Telegram Bot
- Open the Telegram Bot chat (or run bot integration handlers).
- The patient starts interaction by clicking `/start` or typing a message.

### Step 3: Upload Prescription
- In the Telegram Bot chat, upload a picture of a patient prescription.

### Step 4: Show OCR Extraction
- The AAROGYA backend triggers vision analysis via Gemini models.
- The bot replies with parsed medical details (e.g., diagnosis, prescribed medications, dosage details).

### Step 5: Show Reminder Generation
- The agent graph schedules reminder alerts.
- The bot prompts the patient to configure automatic daily check-in alarms.

### Step 6: Open Dashboard Patients
- Go back to the Next.js dashboard.
- Navigate to the **Patients** page to verify the patient's record was updated with the latest digital prescription details.

### Step 7: Open MCP Tools
- On the dashboard's side navigation bar, click on **MCP Tools** (🧩).
- This displays the Model Context Protocol console in a clean, light healthcare theme.

### Step 8: Search Patient
- Copy a patient UUID from the **Patients** list or quick-select list.
- Paste it into the Patient Lookup search box and click **Search Patient**.

### Step 9: Show Risk Assessment
- View the real-time AI risk assessment meter showing risk score (High/Medium/Low) and key identified health risk factors.

### Step 10: Show Prescriptions
- Review the safety-guarded prescription history panel showing active diagnoses, issue dates, and recognized medicines.

### Step 11: Show Alerts
- Go to the **Alerts** page to view live high-risk alert items currently assigned to doctors or HCWs.

---
**Expected Demo Time:** 2–3 Minutes
