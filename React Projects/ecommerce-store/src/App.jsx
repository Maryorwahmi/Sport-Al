/**
 * E-Commerce Store - Johnson's Store
 * Designed by: CaptianCode
 * 
 * A functional online store with product catalog, cart, and checkout
 */

import { useState } from 'react'
import './App.css'

function App() {
  const [activeView, setActiveView] = useState('home')
  const [cart, setCart] = useState([])

  // Sample products
  const products = [
    { id: 1, name: 'Wireless Headphones', price: 79.99, category: 'Electronics', image: '🎧' },
    { id: 2, name: 'Smart Watch', price: 199.99, category: 'Electronics', image: '⌚' },
    { id: 3, name: 'Running Shoes', price: 89.99, category: 'Sports', image: '👟' },
    { id: 4, name: 'Backpack', price: 49.99, category: 'Accessories', image: '🎒' },
    { id: 5, name: 'Coffee Maker', price: 129.99, category: 'Home', image: '☕' },
    { id: 6, name: 'Yoga Mat', price: 29.99, category: 'Sports', image: '🧘' },
  ]

  const addToCart = (product) => {
    setCart([...cart, product])
  }

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.id !== productId))
  }

  const getTotalPrice = () => {
    return cart.reduce((total, item) => total + item.price, 0).toFixed(2)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-md sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-purple-600 text-white rounded-full w-10 h-10 flex items-center justify-center text-2xl">
                🛍️
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">Johnson's Store</h1>
                <p className="text-xs text-gray-500">Your Online Shopping Destination</p>
              </div>
            </div>
            <nav className="flex items-center space-x-4">
              <button 
                onClick={() => setActiveView('home')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeView === 'home' 
                    ? 'bg-purple-600 text-white' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Home
              </button>
              <button 
                onClick={() => setActiveView('products')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeView === 'products' 
                    ? 'bg-purple-600 text-white' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Products
              </button>
              <button 
                onClick={() => setActiveView('cart')}
                className={`px-4 py-2 rounded-lg transition-colors relative ${
                  activeView === 'cart' 
                    ? 'bg-purple-600 text-white' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Cart
                {cart.length > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">
                    {cart.length}
                  </span>
                )}
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeView === 'home' && (
          <div>
            {/* Hero Section */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg shadow-lg p-12 mb-8 text-white">
              <h2 className="text-4xl font-bold mb-4">Welcome to Johnson's Store</h2>
              <p className="text-xl mb-6">
                Discover amazing products at unbeatable prices!
              </p>
              <button 
                onClick={() => setActiveView('products')}
                className="bg-white text-purple-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Shop Now
              </button>
            </div>

            {/* Features */}
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-md text-center">
                <div className="text-4xl mb-3">🚚</div>
                <h3 className="font-bold text-lg mb-2">Free Shipping</h3>
                <p className="text-gray-600 text-sm">On orders over $50</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md text-center">
                <div className="text-4xl mb-3">💳</div>
                <h3 className="font-bold text-lg mb-2">Secure Payment</h3>
                <p className="text-gray-600 text-sm">Stripe & Paystack integration</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md text-center">
                <div className="text-4xl mb-3">⭐</div>
                <h3 className="font-bold text-lg mb-2">Quality Products</h3>
                <p className="text-gray-600 text-sm">100% satisfaction guaranteed</p>
              </div>
            </div>

            {/* Featured Products Preview */}
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-6">Featured Products</h3>
              <div className="grid md:grid-cols-3 gap-6">
                {products.slice(0, 3).map(product => (
                  <div key={product.id} className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                    <div className="text-6xl text-center mb-4">{product.image}</div>
                    <h4 className="font-bold text-lg mb-2">{product.name}</h4>
                    <p className="text-gray-600 text-sm mb-3">{product.category}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-purple-600 font-bold text-xl">${product.price}</span>
                      <button 
                        onClick={() => addToCart(product)}
                        className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
                      >
                        Add to Cart
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeView === 'products' && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-6">All Products</h2>
            <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-6">
              {products.map(product => (
                <div key={product.id} className="bg-white border rounded-lg p-4 hover:shadow-lg transition-shadow">
                  <div className="text-6xl text-center mb-4">{product.image}</div>
                  <h4 className="font-bold text-lg mb-2">{product.name}</h4>
                  <p className="text-gray-600 text-sm mb-3">{product.category}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-purple-600 font-bold text-xl">${product.price}</span>
                    <button 
                      onClick={() => addToCart(product)}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors text-sm"
                    >
                      Add to Cart
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeView === 'cart' && (
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-800 mb-6">Shopping Cart</h2>
            {cart.length === 0 ? (
              <div className="bg-white rounded-lg shadow-lg p-12 text-center">
                <div className="text-6xl mb-4">🛒</div>
                <p className="text-gray-600 text-xl mb-6">Your cart is empty</p>
                <button 
                  onClick={() => setActiveView('products')}
                  className="bg-purple-600 text-white px-8 py-3 rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Start Shopping
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-lg p-8">
                <div className="space-y-4 mb-6">
                  {cart.map((item, index) => (
                    <div key={index} className="flex items-center justify-between border-b pb-4">
                      <div className="flex items-center space-x-4">
                        <div className="text-4xl">{item.image}</div>
                        <div>
                          <h4 className="font-bold">{item.name}</h4>
                          <p className="text-gray-600 text-sm">{item.category}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="text-purple-600 font-bold text-lg">${item.price}</span>
                        <button 
                          onClick={() => removeFromCart(item.id)}
                          className="text-red-600 hover:text-red-700 font-medium"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-6">
                    <span className="text-xl font-bold">Total:</span>
                    <span className="text-2xl font-bold text-purple-600">${getTotalPrice()}</span>
                  </div>
                  <button className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition-colors font-semibold">
                    Proceed to Checkout
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white mt-12">
        <div className="container mx-auto px-4 py-8">
          <div className="grid md:grid-cols-3 gap-8 mb-6">
            <div>
              <h3 className="font-bold text-lg mb-3">About Johnson's Store</h3>
              <p className="text-gray-400 text-sm">
                Your trusted online shopping destination for quality products at great prices.
              </p>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-3">Quick Links</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><button className="hover:text-white">About Us</button></li>
                <li><button className="hover:text-white">Contact</button></li>
                <li><button className="hover:text-white">Terms & Conditions</button></li>
                <li><button className="hover:text-white">Privacy Policy</button></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-3">Customer Service</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><button className="hover:text-white">FAQs</button></li>
                <li><button className="hover:text-white">Shipping Info</button></li>
                <li><button className="hover:text-white">Returns</button></li>
                <li><button className="hover:text-white">Track Order</button></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-6 text-center">
            <p className="text-gray-400 text-sm">
              Designed by <span className="font-bold text-purple-400">CaptianCode</span>
            </p>
            <p className="text-gray-500 text-xs mt-1">
              E-Commerce Store - Johnson's Store © 2024
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
