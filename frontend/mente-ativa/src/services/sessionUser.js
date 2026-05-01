export const getCurrentUserProfile = () => {
  if (typeof sessionStorage === 'undefined') {
    return null
  }

  const rawProfile = sessionStorage.getItem('userProfile')

  if (!rawProfile) {
    return null
  }

  try {
    return JSON.parse(rawProfile)
  } catch {
    return null
  }
}

export const getUserKey = (profile = getCurrentUserProfile()) => {
  return profile?.uid || null
}