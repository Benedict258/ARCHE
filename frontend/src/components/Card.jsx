import React from 'react'

const Card = ({children, className='', title})=>{
  return (
    <div className={`card ${className}`}>
      {title && <div className="card-title">{title}</div>}
      <div className="card-content">{children}</div>
    </div>
  )
}

export default Card
