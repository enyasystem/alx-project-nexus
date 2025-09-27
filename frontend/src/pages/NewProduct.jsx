import React, { useState } from 'react'
import axios from 'axios'

export default function NewProduct(){
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [price, setPrice] = useState('')
  const [inventory, setInventory] = useState('')
  const [categoryId, setCategoryId] = useState('1')
  const [categories, setCategories] = useState([])
  const [file, setFile] = useState(null)
  const [msg, setMsg] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const fd = new FormData()
    fd.append('name', name)
    fd.append('slug', slug)
    fd.append('price', price)
    fd.append('inventory', inventory)
    fd.append('category_id', categoryId)
    if(file) fd.append('image', file)
    const token = localStorage.getItem('access')
    try{
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/products/`, fd, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })
      setMsg('Product created')
    }catch(err){
      setMsg('Failed')
    }
  }

  // fetch categories
  React.useEffect(()=>{
    let mounted = true
    axios.get(`${import.meta.env.VITE_API_URL}/categories/`).then(res=>{
      if(mounted) setCategories(res.data)
    }).catch(()=>{})
    return ()=> mounted = false
  }, [])

  return (
    <div className="max-w-lg mx-auto bg-white p-6 rounded shadow">
      <h2 className="text-xl font-semibold mb-4">New Product</h2>
      <form onSubmit={handleSubmit}>
        <input className="w-full p-2 border rounded mb-2" placeholder="Name" value={name} onChange={e=>setName(e.target.value)} />
        <input className="w-full p-2 border rounded mb-2" placeholder="Slug" value={slug} onChange={e=>setSlug(e.target.value)} />
        <input className="w-full p-2 border rounded mb-2" placeholder="Price" value={price} onChange={e=>setPrice(e.target.value)} />
        <input className="w-full p-2 border rounded mb-2" placeholder="Inventory" value={inventory} onChange={e=>setInventory(e.target.value)} />
        <select className="w-full p-2 border rounded mb-2" value={categoryId} onChange={e=>setCategoryId(e.target.value)}>
          {categories.map(c=> <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <input type="file" onChange={e=>setFile(e.target.files[0])} className="mb-4" />
        <button className="bg-indigo-600 text-white px-4 py-2 rounded">Create</button>
      </form>
      {msg && <p className="mt-4">{msg}</p>}
    </div>
  )
}
