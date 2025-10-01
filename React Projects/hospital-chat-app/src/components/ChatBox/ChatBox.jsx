/**
 * ChatBox Component - Hospital Chat App
 * Designed by: CaptianCode
 */

import React from 'react';

const ChatBox = ({ messages = [], currentUser = 'user' }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-4 h-96 overflow-y-auto">
      <div className="space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-20">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.sender === currentUser ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-xs px-4 py-2 rounded-lg ${
                  message.sender === currentUser
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-800'
                }`}
              >
                <p className="text-sm font-semibold mb-1">{message.senderName}</p>
                <p>{message.text}</p>
                <p className="text-xs mt-1 opacity-75">{message.time}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ChatBox;
