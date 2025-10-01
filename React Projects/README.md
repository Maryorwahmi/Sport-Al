# React Projects

**Designed by: CaptianCode**

This folder contains two professional React applications showcasing modern web development practices with React.js and Tailwind CSS.

---

## 📁 Projects Overview

### 1. 🏥 Hospital Chat App - Johnson's Health Care

A secure, real-time hospital communication platform for doctors, patients, and staff.

**Key Features:**
- User authentication (Doctor, Patient, Admin roles)
- Real-time chat functionality
- Private 1-to-1 messaging + group chats
- Online/offline status indicators
- Message history stored in database
- Notifications for new messages
- Basic admin control

**Tech Stack:**
- React.js + Vite
- Tailwind CSS
- Context API / Zustand (State Management)
- Socket.io / Firebase (Real-time)
- Node.js + Express (Backend)
- MongoDB / Firebase (Database)

📂 [View Hospital Chat App](./hospital-chat-app/)

---

### 2. 🛍️ E-Commerce Store - Johnson's Store

A functional online store with product catalog, cart, checkout, and payment integration.

**Key Features:**
- Product listing with categories and filters
- Product details page
- Shopping cart (add/remove/update quantities)
- Checkout form with validation
- Payment integration (Stripe/Paystack)
- User authentication and order history
- Admin dashboard for product management

**Tech Stack:**
- React.js + Vite
- Tailwind CSS
- Redux Toolkit / Zustand (State Management)
- React Router (Navigation)
- Node.js + Express / Next.js (Backend)
- MongoDB Atlas (Database)
- Stripe / Paystack (Payments)

📂 [View E-Commerce Store](./ecommerce-store/)

---

## 🚀 Quick Start

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Running the Projects

#### Hospital Chat App

```bash
cd hospital-chat-app
npm install
npm run dev
```

Visit `http://localhost:5173` to view the app.

#### E-Commerce Store

```bash
cd ecommerce-store
npm install
npm run dev
```

Visit `http://localhost:5173` to view the app.

---

## 🛠️ Development

### Building for Production

Both projects use Vite for optimal production builds:

```bash
# In each project directory
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

---

## 📚 Project Structure

Both projects follow a similar, organized structure:

```
project-name/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/          # Page components
│   ├── services/       # API and external services
│   ├── context/        # State management (Context API)
│   ├── store/          # State management (Redux/Zustand)
│   ├── utils/          # Helper functions
│   ├── App.jsx         # Main application component
│   └── main.jsx        # Application entry point
├── public/             # Static assets
├── index.html          # HTML template
├── package.json        # Project dependencies
├── tailwind.config.js  # Tailwind CSS configuration
└── vite.config.js      # Vite configuration
```

---

## ✨ Features

### Common Features
- ✅ Modern React with Hooks
- ✅ Tailwind CSS for styling
- ✅ Responsive design
- ✅ Fast HMR (Hot Module Replacement)
- ✅ Optimized production builds
- ✅ ESLint configuration

### Hospital Chat App Specifics
- Real-time messaging capabilities
- User role management
- Message history and notifications
- HIPAA-compliant security considerations

### E-Commerce Store Specifics
- Shopping cart functionality
- Product catalog management
- Payment processing integration
- Order tracking and history

---

## 🎨 Design Philosophy

Both applications are designed with:
- **User Experience First**: Clean, intuitive interfaces
- **Performance**: Fast load times and smooth interactions
- **Responsiveness**: Works seamlessly on all devices
- **Scalability**: Built to handle growth and additional features
- **Security**: Best practices for data protection

---

## 📖 Documentation

Each project has its own detailed README with:
- Complete feature list
- Technology stack details
- Setup instructions
- API documentation
- Deployment guides

---

## 👤 About the Designer

**CaptianCode** - Full-stack developer specializing in React.js, modern web technologies, and user-centric design.

These projects demonstrate expertise in:
- React.js and modern JavaScript
- Tailwind CSS and responsive design
- State management patterns
- Real-time communication
- E-commerce functionality
- RESTful API integration

---

## 📝 License

These projects are created for portfolio and educational purposes.

---

## 🤝 Contributing

These are demonstration projects, but suggestions and feedback are welcome!

---

**CaptianCode** © 2024 - Designed with ❤️ and ☕
