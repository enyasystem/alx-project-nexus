import React, { createContext, useState, useEffect } from 'react'

export const AuthContext = createContext({
  access: null,
  login: () => {},
  logout: () => {},
  isAuthenticated: false,
})

export function AuthProvider({ children }){
  const [access, setAccess] = useState(() => {
    try{
      return localStorage.getItem('access')
    }catch(e){
      return null
    }
  })

  useEffect(()=>{
    try{
      if(access) localStorage.setItem('access', access)
      else localStorage.removeItem('access')
    }catch(e){}
  }, [access])

  const login = (token)=> setAccess(token)
  const logout = ()=> setAccess(null)

  const value = {
    access,
    login,
    logout,
    isAuthenticated: !!access,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider
