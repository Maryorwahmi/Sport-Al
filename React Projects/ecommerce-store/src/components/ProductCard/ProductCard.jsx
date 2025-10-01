/**
 * ProductCard Component - E-Commerce Store
 * Designed by: CaptianCode
 */

import React from 'react';

const ProductCard = ({ product, onAddToCart }) => {
  return (
    <div className="bg-white border rounded-lg p-4 hover:shadow-lg transition-shadow">
      <div className="text-6xl text-center mb-4">{product.image || '📦'}</div>
      <h4 className="font-bold text-lg mb-2">{product.name}</h4>
      <p className="text-gray-600 text-sm mb-3">{product.category}</p>
      {product.description && (
        <p className="text-gray-500 text-sm mb-3">{product.description}</p>
      )}
      <div className="flex items-center justify-between">
        <span className="text-purple-600 font-bold text-xl">
          ${product.price.toFixed(2)}
        </span>
        <button
          onClick={() => onAddToCart(product)}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors text-sm"
        >
          Add to Cart
        </button>
      </div>
    </div>
  );
};

export default ProductCard;
