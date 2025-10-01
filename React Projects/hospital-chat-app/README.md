# Hospital Chat App - Johnson's Health Care

**Designed by: CaptianCode**

A secure, real-time hospital communication platform for doctors, patients, and staff with focus on chat features, user roles, and message storage.

## 🎯 Goal

Build a secure, real-time hospital communication platform for doctors, patients, and staff. Focus on chat features, user roles, and message storage.

## 🛠 Tech Stack

- **Frontend**: React.js + Tailwind CSS (UI components)
- **State Management**: Context API or Zustand
- **Backend**: Node.js + Express
- **Database**: Firebase (real-time) OR MongoDB + Socket.io
- **Authentication**: Firebase Auth / JWT

## ✨ Features

- User authentication (Doctor, Patient, Admin)
- Real-time chat (Socket.io or Firebase RTDB)
- Private 1-to-1 messaging + group chats
- Online/offline status
- Message history stored in DB
- Notifications for new messages
- Basic admin control (ban/remove users)

## 📋 Project Breakdown

1. **Setup React project** (Vite) + Tailwind CSS ✅
2. **Create authentication** (login, signup, roles)
3. **Build chat UI** → ChatBox, MessageList, MessageInput
4. **Integrate Socket.io or Firebase** for real-time messaging
5. **Store messages** (MongoDB/Firebase)
6. **Add online/offline indicator**

## 🚀 Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

### Build for Production

```bash
npm run build
```

## 📁 Project Structure

```
hospital-chat-app/
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── ChatBox/
│   │   ├── MessageList/
│   │   └── MessageInput/
│   ├── pages/          # Page components
│   │   ├── Login/
│   │   ├── Dashboard/
│   │   └── Chat/
│   ├── services/       # API and Socket services
│   ├── context/        # State management
│   └── utils/          # Helper functions
├── public/             # Static assets
└── package.json
```

## 👤 Author

**CaptianCode** - Designer & Developer

---

*This is a professional hospital communication platform designed with security and user experience in mind.*
