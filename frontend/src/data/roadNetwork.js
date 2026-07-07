/** 北京国贸CBD路网 — 高德交通态势API (GCJ-02)
 *
 * 数据来源: 高德地图 REST API /v3/traffic/status/rectangle
 * 坐标系: GCJ-02，与高德底图完美对齐，无需转换
 * 自动生成: algorithm/fetch_amap_network.py
 */
import roadData from './roadNetwork.json'

const rawSegments = roadData.segments || []

export const ROAD_SEGMENTS = rawSegments.map(seg => ({
  id: seg.id,
  name: seg.name,
  path: seg.path,  // GCJ-02，可直接用于AMap.Polyline
  direction: seg.direction || '',
  speed: seg.speed || 0,
  status: seg.status || 0,
  source: seg.source || 'amap',
}))

console.log(`[roadNetwork] ${ROAD_SEGMENTS.length} Amap roads loaded (GCJ-02)`)

/** 根据occupancy返回颜色 */
export function getCongestionColor(occupancy) {
  if (occupancy == null || occupancy < 0) return '#444444'
  if (occupancy < 30) return '#52c41a'
  if (occupancy < 60) return '#fadb14'
  if (occupancy < 85) return '#fa8c16'
  return '#f5222d'
}

export function getCongestionWidth(occupancy) {
  if (occupancy == null) return 3
  if (occupancy < 30) return 4
  if (occupancy < 60) return 6
  if (occupancy < 85) return 8
  return 10
}

export function getCongestionOpacity(occupancy) {
  if (occupancy == null) return 0.3
  return 0.6 + (occupancy / 100) * 0.35
}
