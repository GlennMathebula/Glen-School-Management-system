# Glen Moniques Student Mobile App

This Expo/React Native app consumes the same FastAPI Student Portal API as the web portal.

## Local development

Backend from `C:\Projects\Glen Moniques SMS\backend`:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Mobile app:

```powershell
cd "C:\Projects\Glen Moniques SMS\frontends\student-mobile"
npx expo start
```

Scan the QR code with Expo Go while the phone and computer are on the same network.

The API base URL is read from `.env`:

```text
EXPO_PUBLIC_API_BASE_URL=http://YOUR-PC-LAN-IP:8000
```

Do not use `localhost` when testing on a physical phone.

## Security

JWT/session metadata is stored with `expo-secure-store`, not browser localStorage.

## Current screens

- Password + PIN authentication
- First-time password/PIN setup
- Dashboard
- Modules
- Results
- FISA / EISA
- Attendance
- Timetable / online class links
- Learning resources
- Document centre + upload
- Finance, invoices, receipts, statement and PayFast starter
- Student card, QR, avatar upload and replacement request
- Completion documents
- Messages / announcements
- Support
- Account / contact / password / PIN
