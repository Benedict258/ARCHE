import React, { useState } from 'react'

const Icon = ({name, size=18, alt})=>{
  const [failed, setFailed] = useState(false)
  const src = `/assets/icons/${name}.svg`
  const fallbackStyle = {
    display:'inline-flex',
    alignItems:'center',
    justifyContent:'center',
    width:size,
    height:size,
    background:'rgba(11,116,255,0.12)',
    borderRadius:8,
    color:'#044',
    fontSize:12,
    fontWeight:600,
    textTransform:'uppercase'
  }

  if(failed){
    return <span style={fallbackStyle} aria-label={alt || name}>{(name?.charAt(0) || 'I')}</span>
  }

  return <img src={src} alt={alt||name} width={size} height={size} style={{display:'inline-block'}} onError={()=>setFailed(true)} />
}

export default Icon
