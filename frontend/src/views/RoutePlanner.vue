<template>
  <div style="color:var(--text-primary);height:calc(100vh - 120px)">
    <h2>路径规划</h2>
    <div style="display:flex;gap:20px;height:calc(100% - 50px)">
      <!-- 左侧：表单 + 结果 -->
      <div style="width:420px;display:flex;flex-direction:column;gap:16px;overflow-y:auto">
        <!-- 表单 -->
        <el-card shadow="never" style="background:var(--bg-panel)">
          <div style="display:flex;flex-direction:column;gap:12px">
            <div>
              <div style="font-size:13px;color:var(--text-secondary);margin-bottom:4px">起点路段</div>
              <el-select v-model="origin" placeholder="选择起点" filterable style="width:100%">
                <el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </div>
            <div>
              <div style="font-size:13px;color:var(--text-secondary);margin-bottom:4px">终点路段</div>
              <el-select v-model="dest" placeholder="选择终点" filterable style="width:100%">
                <el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </div>
            <el-button type="primary" @click="planRoute" :loading="loading" style="width:100%">
              <span v-if="!loading">&#x1F698; 规划路径</span>
              <span v-else>规划中...</span>
            </el-button>
          </div>
        </el-card>

        <!-- 结果 -->
        <el-card v-if="result" shadow="never" style="background:var(--bg-panel)">
          <template #header>
            <span style="font-weight:bold;color:var(--accent-blue)">&#x1F4CD; 规划结果</span>
          </template>
          <div style="display:flex;gap:16px;margin-bottom:16px">
            <div style="flex:1;text-align:center;padding:12px;background:rgba(0,212,255,.08);border-radius:8px">
              <div style="font-size:12px;color:var(--text-secondary)">总距离</div>
              <div style="font-size:24px;font-weight:bold;color:var(--accent-blue)">{{ result.total_distance }} <small>km</small></div>
            </div>
            <div style="flex:1;text-align:center;padding:12px;background:rgba(0,212,255,.08);border-radius:8px">
              <div style="font-size:12px;color:var(--text-secondary)">预计时间</div>
              <div style="font-size:24px;font-weight:bold;color:var(--accent-blue)">{{ result.estimated_time }} <small>min</small></div>
            </div>
          </div>

          <div style="font-size:13px;color:var(--text-secondary);margin-bottom:8px">路径详情 ({{ result.path.length }} 个路段)</div>
          <div v-for="(p, i) in result.path" :key="i" class="route-segment">
            <div class="segment-num">{{ i + 1 }}</div>
            <div class="segment-info">
              <div class="segment-name">{{ p.name }}</div>
              <div class="segment-sub">{{ p.length || 0 }} km
                <span v-if="p.occupancy != null" style="margin-left:8px">
                  <el-tag size="small" :type="p.occupancy < 30 ? 'success' : p.occupancy < 60 ? 'warning' : 'danger'" effect="dark">
                    {{ p.occupancy < 30 ? '畅通' : p.occupancy < 60 ? '缓行' : p.occupancy < 85 ? '拥堵' : '严重' }}
                  </el-tag>
                </span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 预测联动提示 -->
        <el-card v-if="result" shadow="never" style="background:var(--bg-panel)">
          <div style="font-size:13px;color:var(--text-secondary)">
            &#x1F4CA; 想了解这条路径的未来交通状况？
            <el-link type="primary" @click="$router.push('/prediction')" style="font-size:13px">前往流量预测 →</el-link>
          </div>
        </el-card>
      </div>

      <!-- 右侧：地图 -->
      <div style="flex:1;min-width:0">
        <el-card shadow="never" style="height:100%;background:var(--bg-panel)">
          <TrafficMap :route-path="routeCoords" :map-height="'100%'" @section-click="onMapClick" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { routeApi } from '@/api/routePlan'
import { sectionsApi } from '@/api/sections'
import { trafficApi } from '@/api/traffic'
import { ROAD_SEGMENTS } from '@/data/roadNetwork'
import TrafficMap from '@/components/map/TrafficMap.vue'

const sections = ref([])
const origin = ref(null)
const dest = ref(null)
const loading = ref(false)
const result = ref(null)
const routeCoords = ref([])  // 传给 TrafficMap 的路线坐标

onMounted(async () => {
  try {
    const res = await sectionsApi.getList()
    sections.value = res.data?.items || res?.items || []
  } catch {}
})

// 按名称匹配 ROAD_SEGMENTS 获取坐标
const findSegment = (name) => {
  if (!name) return null
  // 精确匹配
  for (const seg of ROAD_SEGMENTS) {
    if (seg.name === name) return seg
  }
  // 子串匹配（高德名含方向后缀）
  for (const seg of ROAD_SEGMENTS) {
    if (seg.name && name && (seg.name.includes(name) || name.includes(seg.name))) return seg
  }
  return null
}

const planRoute = async () => {
  if (!origin.value || !dest.value) return
  loading.value = true
  try {
    const res = await routeApi.plan({
      origin_section_id: origin.value,
      dest_section_id: dest.value,
    })
    const data = res.data || res
    result.value = data

    // 匹配路径坐标 → 传给地图
    const segments = data.path || []
    const coords = []
    for (const p of segments) {
      const seg = findSegment(p.name)
      if (seg) {
        coords.push({ name: p.name, path: seg.path, length: p.length })
      }
    }
    routeCoords.value = coords

    // 获取路径各路段的车流数据
    try {
      const trafficRes = await trafficApi.getCurrent()
      const items = trafficRes.data?.items || trafficRes?.items || trafficRes.data || []
      if (Array.isArray(items)) {
        const trafficMap = {}
        items.forEach(t => { if (t.section_name) trafficMap[t.section_name] = t })
        // 把车流数据注入到result.path中
        for (const p of result.value.path) {
          const td = trafficMap[p.name]
          if (td) {
            p.occupancy = td.occupancy
            p.vehicle_count = td.vehicle_count
            p.avg_speed = td.avg_speed
          }
        }
      }
    } catch {}
  } finally {
    loading.value = false
  }
}

const onMapClick = (data) => {
  // 地图上点击路段可以快速选择为起点/终点
}
</script>

<style scoped>
.route-segment { display:flex; gap:12px; padding:10px 0; border-bottom:1px solid rgba(255,255,255,.04); align-items:flex-start }
.segment-num { width:24px; height:24px; background:rgba(0,212,255,.15); color:var(--accent-blue); border-radius:50%; text-align:center; line-height:24px; font-size:12px; font-weight:bold; flex-shrink:0 }
.segment-info { flex:1 }
.segment-name { font-size:14px; font-weight:500 }
.segment-sub { font-size:12px; color:var(--text-secondary); margin-top:2px }
</style>
