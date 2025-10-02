import { useState } from 'react'

const products = [
  {
    id: 1,
    name: 'Wireless Headphones',
    price: 79.99,
    category: 'Electronics',
    image: 'https://images.unsplash.com/photo-1516707891-8135c3a2a7e7?auto=format&fit=crop&w=400&q=80',
  },
  {
    id: 2,
    name: 'Smart Watch',
    price: 199.99,
    category: 'Electronics',
    image: 'https://images.unsplash.com/photo-1516574187841-cb9cc2ca948b?auto=format&fit=crop&w=400&q=80',
  },
  {
    id: 3,
    name: 'Running Shoes',
    price: 89.99,
    category: 'Sports',
    image: 'https://images.unsplash.com/photo-1519864600581-8f1f89a4f0ac?auto=format&fit=crop&w=400&q=80',
  },
  {
    id: 4,
    name: 'Backpack',
    price: 49.99,
    category: 'Accessories',
    image: 'https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80',
  },
  {
    id: 5,
    name: 'Coffee Maker',
    price: 129.99,
    category: 'Home',
    image: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=400&q=80',
  },
  {
    id: 6,
    name: 'Yoga Mat',
    price: 29.99,
    category: 'Sports',
    image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80',
  },
]

function App() {
  const [activeView, setActiveView] = useState('home')
  const [cart, setCart] = useState([])

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
    <div className="min-h-screen bg-gradient-to-br from-purple-100 to-pink-100 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-lg sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <img src="https://img.icons8.com/color/96/000000/shop.png" alt="Logo" className="w-12 h-12 rounded-full shadow-lg" />
            <div>
              <h1 className="text-2xl font-extrabold text-purple-700">Johnson's Store</h1>
              <p className="text-xs text-gray-500">Your Online Shopping Destination</p>
            </div>
          </div>
          <nav className="flex items-center space-x-2">
            <button 
              onClick={() => setActiveView('home')}
              className={`px-5 py-2 rounded-lg font-semibold transition #{
                activeView === 'home' 
                  ? 'bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-md'
                  : 'text-purple-700 hover:bg-purple-100'
              }`}
            >
              Home
            </button>
            <button 
              onClick={() => setActiveView('products')}
              className={`px-5 py-2 rounded-lg font-semibold transition #{
                activeView === 'products' 
                  ? 'bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-md'
                  : 'text-purple-700 hover:bg-purple-100'
              }`}
            >
              Products
            </button>
            <button 
              onClick={() => setActiveView('cart')}
              className={`px-5 py-2 rounded-lg font-semibold transition relative #{
                activeView === 'cart' 
                  ? 'bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-md'
                  : 'text-purple-700 hover:bg-purple-100'
              }`}
            >
              Cart
              {cart.length > 0 && (
                <span className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs border-2 border-white font-bold">
                  {cart.length}
                </span>
              )}
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-10">
        {activeView === 'home' && (
          <section>
            {/* Hero Section */}
            <div className="relative rounded-xl overflow-hidden shadow-2xl mb-10">
              <img 
                src="https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=1200&q=80"
                alt="Shopping"
                className="w-full h-72 object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-purple-700 via-pink-500 to-transparent opacity-80 flex flex-col justify-center items-start p-10">
                <h2 className="text-5xl font-extrabold text-white drop-shadow-lg mb-4">Welcome to Johnson's Store</h2>
                <p className="text-2xl text-white mb-6 drop-shadow">
                  Discover amazing products at unbeatable prices!
                </p>
                <button 
                  onClick={() => setActiveView('products')}
                  className="bg-white text-purple-700 px-8 py-4 rounded-lg font-bold shadow-lg hover:bg-purple-100 hover:text-purple-900 transition"
                >
                  Shop Now
                </button>
              </div>
            </div>

            {/* Features */}
            <div className="grid md:grid-cols-3 gap-8 mb-10">
              <div className="bg-white p-8 rounded-xl shadow hover:shadow-xl text-center transition">
                <img src="https://img.icons8.com/color/96/000000/delivery.png" alt="Free Shipping" className="mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2 text-purple-700">Free Shipping</h3>
                <p className="text-gray-600">On orders over #50</p>
              </div>
              <div className="bg-white p-8 rounded-xl shadow hover:shadow-xl text-center transition">
                <img src="https://img.icons8.com/color/96/000000/bank-card-back-side.png" alt="Secure Payment" className="mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2 text-purple-700">Secure Payment</h3>
                <p className="text-gray-600">Stripe & Paystack integration</p>
              </div>
              <div className="bg-white p-8 rounded-xl shadow hover:shadow-xl text-center transition">
                <img src="https://img.icons8.com/color/96/000000/star.png" alt="Quality Products" className="mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2 text-purple-700">Quality Products</h3>
                <p className="text-gray-600">100% satisfaction guaranteed</p>
              </div>
            </div>

            {/* Featured Products Preview */}
            <div className="bg-white rounded-xl shadow-2xl p-10 mb-10">
              <h3 className="text-3xl font-extrabold text-purple-800 mb-8">Featured Products</h3>
              <div className="grid md:grid-cols-3 gap-8">
                {products.slice(0, 3).map(product => (
                  <div key={product.id} className="bg-gradient-to-br from-pink-100 to-purple-100 border border-purple-200 rounded-xl p-6 flex flex-col hover:shadow-xl transition">
                    <img src={product.image} alt={product.name} className="w-full h-48 object-cover rounded-lg mb-4 shadow" />
                    <h4 className="font-bold text-lg mb-2 text-purple-700">{product.name}</h4>
                    <p className="text-gray-500 mb-3">{product.category}</p>
                    <div className="flex items-center justify-between mt-auto">
                      <span className="text-pink-700 font-bold text-xl">#{product.price}</span>
                      <button 
                        onClick={() => addToCart(product)}
                        className="bg-gradient-to-r from-purple-600 to-pink-500 text-white px-5 py-2 rounded-lg hover:scale-105 font-semibold transition"
                      >
                        Add to Cart
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {activeView === 'products' && (
          <section>
            <h2 className="text-4xl font-extrabold text-purple-800 mb-8">All Products</h2>
            <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-8">
              {products.map(product => (
                <div key={product.id} className="bg-white border border-purple-200 rounded-xl p-6 flex flex-col hover:shadow-2xl transition">
                  <img src={product.image} alt={product.name} className="w-full h-40 object-cover rounded-lg mb-4 shadow" />
                  <h4 className="font-bold text-lg mb-2 text-purple-700">{product.name}</h4>
                  <p className="text-gray-500 mb-3">{product.category}</p>
                  <div className="flex items-center justify-between mt-auto">
                    <span className="text-pink-700 font-bold text-xl">#{product.price}</span>
                    <button 
                      onClick={() => addToCart(product)}
                      className="bg-gradient-to-r from-purple-600 to-pink-500 text-white px-4 py-2 rounded-lg hover:scale-105 font-semibold transition text-sm"
                    >
                      Add to Cart
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {activeView === 'cart' && (
          <section className="max-w-4xl mx-auto">
            <h2 className="text-4xl font-extrabold text-purple-800 mb-8">Shopping Cart</h2>
            {cart.length === 0 ? (
              <div className="bg-white rounded-xl shadow-2xl p-16 text-center">
                <img src="https://img.icons8.com/color/96/000000/shopping-cart.png" alt="Empty Cart" className="mx-auto mb-6" />
                <p className="text-purple-700 text-2xl mb-8 font-bold">Your cart is empty</p>
                <button 
                  onClick={() => setActiveView('products')}
                  className="bg-gradient-to-r from-purple-600 to-pink-500 text-white px-8 py-4 rounded-lg font-bold hover:scale-105 shadow-lg transition"
                >
                  Start Shopping
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-2xl p-10">
                <div className="space-y-6 mb-8">
                  {cart.map((item, index) => (
                    <div key={index} className="flex items-center justify-between border-b pb-6">
                      <div className="flex items-center space-x-6">
                        <img src={item.image} alt={item.name} className="w-16 h-16 object-cover rounded-lg shadow" />
                        <div>
                          <h4 className="font-bold text-lg text-purple-700">{item.name}</h4>
                          <p className="text-gray-500 text-sm">{item.category}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-6">
                        <span className="text-pink-700 font-bold text-xl">#{item.price}</span>
                        <button 
                          onClick={() => removeFromCart(item.id)}
                          className="text-red-600 hover:text-red-700 font-semibold px-3 py-1 rounded hover:bg-red-100 transition"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="border-t pt-6">
                  <div className="flex items-center justify-between mb-8">
                    <span className="text-2xl font-extrabold text-purple-700">Total:</span>
                    <span className="text-3xl font-extrabold text-pink-700">#{getTotalPrice()}</span>
                  </div>
                  <button className="w-full bg-gradient-to-r from-purple-600 to-pink-500 text-white py-4 rounded-lg font-bold text-xl hover:scale-105 shadow-lg transition">
                    Proceed to Checkout
                  </button>
                </div>
              </div>
            )}
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gradient-to-br from-purple-800 to-pink-800 text-white mt-16 shadow-inner">
        <div className="container mx-auto px-6 py-12">
          <div className="grid md:grid-cols-3 gap-10 mb-8">
            <div>
              <h3 className="font-bold text-xl mb-4">About Johnson's Store</h3>
              <p className="text-purple-200 text-sm">
                Your trusted online shopping destination for quality products at great prices. Shop with confidence!
              </p>
              <div className="flex space-x-3 mt-4">
                <a href="#" aria-label="Facebook">
                  <img src="https://img.icons8.com/color/48/facebook.png" alt="Facebook" className="w-8 h-8"/>
                </a>
                <a href="#" aria-label="Instagram">
                  <img src="https://img.icons8.com/color/48/instagram-new.png" alt="Instagram" className="w-8 h-8"/>
                </a>
                <a href="#" aria-label="Twitter">
                  <img src="https://img.icons8.com/color/48/twitter.png" alt="Twitter" className="w-8 h-8"/>
                </a>
              </div>
            </div>
            <div>
              <h3 className="font-bold text-xl mb-4">Quick Links</h3>
              <ul className="space-y-2 text-sm text-purple-200">
                <li><button className="hover:text-white">About Us</button></li>
                <li><button className="hover:text-white">Contact</button></li>
                <li><button className="hover:text-white">Terms & Conditions</button></li>
                <li><button className="hover:text-white">Privacy Policy</button></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-xl mb-4">Customer Service</h3>
              <ul className="space-y-2 text-sm text-purple-200">
                <li><button className="hover:text-white">FAQs</button></li>
                <li><button className="hover:text-white">Shipping Info</button></li>
                <li><button className="hover:text-white">Returns</button></li>
                <li><button className="hover:text-white">Track Order</button></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-purple-700 pt-8 text-center">
            <p className="text-purple-300 text-sm">
              Designed by <span className="font-bold text-pink-200">CaptianCode</span>
            </p>
            <p className="text-purple-400 text-xs mt-1">
              E-Commerce Store - Johnson's Store © {new Date().getFullYear()}
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
