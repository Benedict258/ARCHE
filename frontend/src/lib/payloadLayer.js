function parseJsonInput(jsonInput){
  const raw = (jsonInput || '').trim()
  if(!raw){
    return {}
  }
  return JSON.parse(raw)
}

export function buildTaskARequest({inputMode, textInput, jsonInput, entries, userToken}){
  if(inputMode === 'text'){
    return {
      raw_input: (textInput || '').trim(),
      output_format: 'text'
    }
  }

  if(inputMode === 'json'){
    return parseJsonInput(jsonInput)
  }

  return {
    user_token: userToken,
    user_history: entries.reviewText
      ? [{
        item_name: entries.previousItemName || 'Previous Item',
        item_category: entries.previousItemCategory || 'general',
        rating: Number(entries.previousRating || 4),
        review_text: entries.reviewText
      }]
      : [],
    item: {
      name: entries.itemName || 'ARCHE Demo Item',
      category: entries.itemCategory || 'general',
      price_tier: entries.priceTier || 'mid',
      attributes: {
        source: 'entries_mode'
      }
    },
    context: {
      time_of_day: entries.timeOfDay || 'evening',
      region: entries.region || 'Lagos'
    },
    forced_rating: entries.forcedRating ? Number(entries.forcedRating) : undefined,
    output_format: 'json'
  }
}

export function buildTaskBRecommendRequest({inputMode, textInput, jsonInput, entries, userToken}){
  if(inputMode === 'text'){
    return {
      raw_input: (textInput || '').trim(),
      output_format: 'text'
    }
  }

  if(inputMode === 'json'){
    return parseJsonInput(jsonInput)
  }

  let itemPool = undefined
  if(entries.itemPoolJson){
    try{
      itemPool = JSON.parse(entries.itemPoolJson)
    }catch(e){
      console.error('Invalid item pool JSON', e)
    }
  }

  return {
    user_token: userToken,
    n: Number(entries.n || 5),
    domain_filter: entries.domainFilter || undefined,
    item_pool: itemPool,
    context: {
      time_bucket: entries.timeBucket || 'evening',
      entry_point: entries.entryPoint || 'web'
    },
    output_format: 'json'
  }
}

export function buildTaskBExplainRequest({inputMode, textInput, jsonInput, entries, userToken, recommendationId}){
  if(inputMode === 'json'){
    return parseJsonInput(jsonInput)
  }

  if(inputMode === 'text'){
    const source = (textInput || '').trim()
    const recMatch = source.match(/rec_[\w-]+/i)
    const tokenMatch = source.match(/user[_\w-]*/i)
    return {
      user_token: tokenMatch ? tokenMatch[0] : userToken,
      recommendation_id: recMatch ? recMatch[0] : recommendationId
    }
  }

  return {
    user_token: userToken,
    recommendation_id: entries.recommendationId || recommendationId
  }
}

export function formatResponseForDisplay(payload){
  if(payload == null){
    return ''
  }
  if(typeof payload === 'string'){
    return payload
  }
  if(typeof payload.raw === 'string'){
    return payload.raw
  }
  if(payload.error){
    return `Error: ${payload.error}${payload.statusCode ? ` (HTTP ${payload.statusCode})` : ''}`
  }
  return JSON.stringify(payload, null, 2)
}