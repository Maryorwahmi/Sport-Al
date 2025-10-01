/**
 * CartItem Component - E-Commerce Store
 * Designed by: CaptianCode
 */

import React from 'react';

const CartItem = ({ item, onRemove, onUpdateQuantity }) => {
  return (
    <div className="flex items-center justify-between border-b pb-4 mb-4">
      <div className="flex items-center space-x-4">
        <div className="text-4xl">{item.image || '📦'}</div>
        <div>
          <h4 className="font-bold">{item.name}</h4>
          <p className="text-gray-600 text-sm">{item.category}</p>
          <p className="text-purple-600 font-bold mt-1">${item.price.toFixed(2)}</p>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        {onUpdateQuantity && (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onUpdateQuantity(item.id, -1)}
              className="bg-gray-200 px-3 py-1 rounded hover:bg-gray-300"
            >
              -
            </button>
            <span className="font-semibold">{item.quantity || 1}</span>
            <button
              onClick={() => onUpdateQuantity(item.id, 1)}
              className="bg-gray-200 px-3 py-1 rounded hover:bg-gray-300"
            >
              +
            </button>
          </div>
        )}
        <button
          onClick={() => onRemove(item.id)}
          className="text-red-600 hover:text-red-700 font-medium"
        >
          Remove
        </button>
      </div>
    </div>
  );
};

export default CartItem;
