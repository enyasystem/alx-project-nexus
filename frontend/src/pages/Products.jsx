import React, { useEffect, useState } from 'react'
import axios from 'axios'

export default function Products(){
  const [products, setProducts] = useState([])
  const [search, setSearch] = useState('')

  const fetchProducts = async () => {
    const url = `${import.meta.env.VITE_API_URL}/products/?search=${encodeURIComponent(search)}`
    const res = await axios.get(url)
    setProducts(res.data.results || res.data)
  }

  useEffect(()=>{ fetchProducts() }, [])

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <input placeholder="Search" value={search} onChange={e=>setSearch(e.target.value)} className="p-2 border rounded flex-1" />
        <button onClick={fetchProducts} className="bg-indigo-600 text-white px-4 py-2 rounded">Search</button>
      </div>
      <div className="grid grid-cols-3 gap-4">
        {products.map(p=> (
          <div key={p.id} className="bg-white p-4 rounded shadow">
            {p.image && <img src={p.image} alt={p.name} className="w-full h-40 object-cover mb-2" />}
            <h3 className="font-semibold">{p.name}</h3>
            <p className="text-sm text-gray-600">${p.price}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
