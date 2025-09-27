import React, { useState, useContext } from 'react'
import axios from 'axios'
import { AuthContext } from '../AuthContext'

export default function Login(){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [msg, setMsg] = useState(null)
  const { login } = useContext(AuthContext)

  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/token/`, { username, password })
      login(res.data.access)
      setMsg('Logged in')
    } catch(err){
      setMsg('Login failed')
    }
  }

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded shadow">
      <h2 className="text-xl font-semibold mb-4">Login</h2>
      <form onSubmit={handleLogin}>
        <label className="block mb-2">Username
          <input value={username} onChange={e=>setUsername(e.target.value)} className="w-full mt-1 p-2 border rounded" />
        </label>
        <label className="block mb-2">Password
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} className="w-full mt-1 p-2 border rounded" />
        </label>
        <button className="bg-indigo-600 text-white px-4 py-2 rounded">Login</button>
      </form>
      {msg && <p className="mt-4">{msg}</p>}
    </div>
  )
}
