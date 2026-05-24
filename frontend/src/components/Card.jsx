import React from 'react'

const Card = ({children, className='', title})=>{
  return (
    <div className={`card ${className}`} style={{padding:18}}>
      {title && <div style={{fontWeight:600,marginBottom:8}}>{title}</div>}
      <div>{children}</div>
    </div>
  )
}

export default Card
