import React, { useContext } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import Login from './pages/Login'
import Products from './pages/Products'
import NewProduct from './pages/NewProduct'
import { AuthContext } from './AuthContext'

export default function App(){
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="bg-white shadow">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold">Project Nexus</Link>
          <nav className="space-x-4">
            <Link to="/products" className="text-sm">Products</Link>
            <Link to="/products/new" className="text-sm">New Product</Link>
            <Link to="/login" className="text-sm">Login</Link>
            <a href="https://enyasystem.github.io/alx-project-nexus/" className="text-sm">API Docs</a>
          </nav>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/new" element={<Protected><NewProduct /></Protected>} />
        </Routes>
      </main>
    </div>
  )
}

function Protected({ children }){
  const { isAuthenticated } = useContext(AuthContext)
  if(!isAuthenticated){
    return <div className="max-w-md mx-auto p-6 bg-white rounded shadow">Please <a href="/login" className="text-indigo-600">login</a> to continue.</div>
  }
  return children
}
