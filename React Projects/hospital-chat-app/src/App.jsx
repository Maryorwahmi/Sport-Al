/**
 * Hospital Chat App - Johnson's Health Care
 * Designed by: CaptianCode
 * 
 * A secure, real-time hospital communication platform
 */

import { useState } from 'react'
import './App.css'

function App() {
  const [activeView, setActiveView] = useState('home')

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">Johnson's Health Care</h1>
                <p className="text-xs text-gray-500">Hospital Chat System</p>
              </div>
            </div>
            <nav className="flex space-x-4">
              <button 
                onClick={() => setActiveView('home')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeView === 'home' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Home
              </button>
              <button 
                onClick={() => setActiveView('login')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeView === 'login' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Login
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeView === 'home' && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">
                Welcome to Johnson's Health Care Chat Platform
              </h2>
              <p className="text-gray-600 mb-6">
                A secure, real-time communication platform designed for healthcare professionals, 
                patients, and staff to collaborate effectively.
              </p>
              
              <div className="grid md:grid-cols-3 gap-6 mt-8">
                <div className="bg-blue-50 p-6 rounded-lg">
                  <div className="bg-blue-600 text-white rounded-full w-12 h-12 flex items-center justify-center mb-4">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                  <h3 className="font-bold text-lg mb-2">Real-time Chat</h3>
                  <p className="text-sm text-gray-600">
                    Instant messaging for doctors, patients, and staff
                  </p>
                </div>
                
                <div className="bg-green-50 p-6 rounded-lg">
                  <div className="bg-green-600 text-white rounded-full w-12 h-12 flex items-center justify-center mb-4">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </div>
                  <h3 className="font-bold text-lg mb-2">Secure & Private</h3>
                  <p className="text-sm text-gray-600">
                    HIPAA-compliant with end-to-end encryption
                  </p>
                </div>
                
                <div className="bg-purple-50 p-6 rounded-lg">
                  <div className="bg-purple-600 text-white rounded-full w-12 h-12 flex items-center justify-center mb-4">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                  </div>
                  <h3 className="font-bold text-lg mb-2">Notifications</h3>
                  <p className="text-sm text-gray-600">
                    Never miss important messages
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-lg p-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-4">Key Features</h3>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3">✓</span>
                  <span className="text-gray-700">User authentication (Doctor, Patient, Admin roles)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3">✓</span>
                  <span className="text-gray-700">Real-time chat with Socket.io or Firebase RTDB</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3">✓</span>
                  <span className="text-gray-700">Private 1-to-1 messaging + group chats</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3">✓</span>
                  <span className="text-gray-700">Online/offline status indicators</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3">✓</span>
                  <span className="text-gray-700">Message history stored in database</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3">✓</span>
                  <span className="text-gray-700">Notifications for new messages</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3">✓</span>
                  <span className="text-gray-700">Basic admin control (ban/remove users)</span>
                </li>
              </ul>
            </div>
          </div>
        )}

        {activeView === 'login' && (
          <div className="max-w-md mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Login</h2>
              <form className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your email"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your password"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Role
                  </label>
                  <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option value="patient">Patient</option>
                    <option value="doctor">Doctor</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <button
                  type="submit"
                  className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Sign In
                </button>
              </form>
              <p className="text-center text-sm text-gray-600 mt-4">
                Don't have an account? <button className="text-blue-600 hover:underline">Sign up</button>
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="container mx-auto px-4 py-6 text-center">
          <p className="text-gray-600 text-sm">
            Designed by <span className="font-bold text-blue-600">CaptianCode</span>
          </p>
          <p className="text-gray-500 text-xs mt-1">
            Hospital Chat App - Johnson's Health Care © 2024
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
