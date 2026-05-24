import React from 'react'

const Icon = ({name, size=18, alt})=>{
  const src = `/assets/icons/${name}.svg`
  const fallbackStyle = {display:'inline-flex',alignItems:'center',justifyContent:'center',width:size,height:size,background:'rgba(11,116,255,0.12)',borderRadius:8,color:'#044',fontSize:12}
  return (
    <img src={src} alt={alt||name} width={size} height={size} style={{display:'inline-block'}} onError={(e)=>{e.currentTarget.onerror=null; e.currentTarget.replaceWith(document.createElement('span')).textContent = (name?.charAt(0)||'I')}}/>
  )
}

export default Icon
