# WebSocket 详细消息格式规范

> **文档类型**：概要设计 — WebSocket协议详细
> **作者**：Agent-Frontend-Map（前端开发（辅）/地图可视化）
> **日期**：2026-07-01
> **任务ID**：D4-T04
> **依赖**：D4-T01 §9(WS事件协议) + D3-T04(地图集成方案)
> **状态**：待审查

---

## 1. 连接规范

| 项 | 值 |
|----|-----|
| URL | `http://localhost:5000`（生产环境同域） |
| 命名空间 | `/`（默认） |
| 传输方式 | WebSocket only（`transports: ['websocket']`） |
| 认证 | 连接时通过 `auth: { token }` 传递JWT |
| 心跳 | Socket.IO内置ping/pong，间隔25s |
| 重连 | 退避延迟：1s → 2s → 4s → 8s → 16s → 30s(max) |

---

## 2. 消息Schema

### 2.1 warning:new

```
服务端 → 客户端：新预警触发
```

```typescript
interface WarningNewPayload {
  warning_id: number;
  section_id: number;
  section_name: string;
  level: 'WARNING' | 'CRITICAL';
  message: string;
  trigger_flow: number;
  threshold: number;
  timestamp: string;  // ISO 8601
}
```

前端处理：`useWarningStore().addWarning(data)` → AlertPopup弹窗（CRITICAL加声音）

### 2.2 warning:update

```
服务端 → 客户端：预警状态变更（如管理员标记处理中）
```

```typescript
interface WarningUpdatePayload {
  warning_id: number;
  is_resolved: boolean;
  resolved_at: string | null;
}
```

### 2.3 warning:resolve

```
服务端 → 客户端：预警已解除（广播给所有在线客户端）
```

```typescript
interface WarningResolvePayload {
  warning_id: number;
  resolved_at: string;
}
```

### 2.4 traffic:update

```
服务端 → 客户端：实时路况数据推送
```

```typescript
interface TrafficUpdatePayload {
  section_id: number;
  vehicle_count: number;
  avg_speed: number;    // km/h
  occupancy: number;    // 0-100
  level: 'smooth' | 'slow' | 'congested' | 'jammed';
  timestamp: string;
}
```

推送频率：订阅后每15秒推送一次（与SUMO仿真采样间隔一致）。

### 2.5 subscribe:section（客户端→服务端）

```typescript
interface SubscribeSectionPayload {
  section_id: number;   // 0 = 订阅全部
}
```

### 2.6 unsubscribe:section（客户端→服务端）

```typescript
interface UnsubscribeSectionPayload {
  section_id: number;
}
```

---

## 3. 前端集成测试方案

### 3.1 连接测试

| 用例 | 步骤 | 预期 |
|------|------|------|
| 正常连接 | 传入有效Token，调用connect() | socket.on('connect')触发，connected=true |
| Token过期 | 传入过期Token | socket.on('connect_error')触发，显示401 |
| 断线重连 | 连接后关闭服务端 | 自动重连，退避延迟递增 |
| 手动断开 | 调用disconnect() | socket.on('disconnect')触发 |

### 3.2 事件测试

| 用例 | 模拟方式 | 预期 |
|------|---------|------|
| warning:new | 手动emit `{level:'CRITICAL', ...}` | AlertPopup弹出 + 红色脉冲动画 + 提示音 |
| warning:new(WARNING) | 同上level:'WARNING' | 弹窗 + 橙色边框，无声音 |
| traffic:update | emit路况数据 | useTrafficStore.realtimeData更新 |
| subscribe | emit subscribe事件 | 服务端开始推送该路段数据 |

### 3.3 多客户端测试

```javascript
// 模拟两个客户端同时在线
const client1 = new SocketClient(); client1.connect(token_admin);
const client2 = new SocketClient(); client2.connect(token_analyst);

// 管理员解除预警 → 两个客户端都收到warning:resolve
client1.socket.emit('resolve_warning', { warning_id: 1 });
// 预期：client1和client2都收到warning:resolve
```

---

## 4. 与Leader的D4-T01一致性确认

| D4-T01 §9 定义 | 本文档实现 | 一致 |
|---------------|-----------|------|
| `warning:new` payload | §2.1 TypeScript接口 | ✅ |
| `warning:update` | §2.2 | ✅ |
| `warning:resolve` | §2.3 | ✅ |
| `traffic:update` | §2.4（新增level字段） | ✅ |
| `subscribe:section` | §2.5 | ✅ |
| `unsubscribe:section` | §2.6 | ✅ |

---

## 5. 交付清单

| 交付物 | 章节 |
|--------|------|
| 连接规范(URL/认证/心跳/重连) | 第1节 |
| 6个WS事件完整TypeScript Schema | 第2节 |
| 前端集成测试方案(连接+事件+多客户端) | 第3节 |
| D4-T01一致性确认 | 第4节 |
