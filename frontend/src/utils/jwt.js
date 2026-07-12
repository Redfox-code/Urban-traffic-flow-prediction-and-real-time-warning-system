/**
 * JWT 工具函数 — 解析 token 获取 payload
 * JWT 格式：header.payload.signature
 */
export function parseJWT(token) {
  if (!token) return null
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = parts[1]
    // Base64 URL-safe decode
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const jsonStr = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonStr)
  } catch {
    return null
  }
}

/**
 * 从 JWT 中提取 role 字段
 * 返回 role 字符串，若无则返回 null
 */
export function getRoleFromToken(token) {
  const payload = parseJWT(token)
  return payload?.role || null
}
