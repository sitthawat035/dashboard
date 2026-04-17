# Refactoring Plan — OpenClaw Dashboard

> สร้างเมื่อ: เมษายน 2026
> เป้าหมาย: แก้ปัญหา state duplication, prop drilling, และ improve code organization

---

## ภาพรวมปัญหา

1. **State Duplication** — state อยู่ทั้งใน hooks และ Zustand store
2. **Prop Drilling** — ส่ง props ลึกหลายชั้น
3. **Socket Event Duplication** — จัดการ socket events หลายที่
4. **Missing TypeScript Types** — ใช้ `any` เยอะเกินไป
5. **Large Components** — บาง component ใหญ่เกินไป

---

## Phase 1: Consolidate State to Zustand Store
**ระยะเวลา:** 2-3 วัน
**ความเสี่ยง:** ต่ำ
**Branch:** `refactor/phase-1-state-consolidation`

### เป้าหมาย
- ลบ state duplication ระหว่าง hooks และ store
- ใช้ Zustand store เป็น single source of truth

### ขั้นตอน

#### 1.1 ย้าย useLogStream state ไป store
- [ ] ลบ `logData` state จาก `useLogStream.ts`
- [ ] เปลี่ยน `setLogData` ใน hook ให้เรียก store แทน
- [ ] แก้ `App.tsx` ลบ sync effect สำหรับ `logData`
- [ ] แก้ component ที่ใช้ `logData` ให้ดึงจาก store

**ไฟล์ที่แก้:**
- `src/hooks/useLogStream.ts`
- `src/App.tsx`
- `src/stores/useAppStore.ts`

#### 1.2 ย้าย useSubagents state ไป store
- [ ] ลบ `subagentLogs` state จาก `useSubagents.ts`
- [ ] เปลี่ยน `setSubagentLogs` ใน hook ให้เรียก store แทน
- [ ] แก้ `App.tsx` ลบ sync effect สำหรับ `subagentLogs`
- [ ] แก้ component ที่ใช้ `subagentLogs` ให้ดึงจาก store

**ไฟล์ที่แก้:**
- `src/hooks/useSubagents.ts`
- `src/App.tsx`

#### 1.3 ย้าย useAuth state ไป store
- [ ] ลบ `isLoggedIn` state จาก `useAuth.ts`
- [ ] เปลี่ยน `setIsLoggedIn` ใน hook ให้เรียก store แทน
- [ ] แก้ `App.tsx` ลบ sync effect สำหรับ `isLoggedIn`

**ไฟล์ที่แก้:**
- `src/hooks/useAuth.ts`
- `src/App.tsx`

#### 1.4 ลบ Sync Effects จาก App.tsx
- [ ] ลบ useEffect ที่ sync `logData` ไป store
- [ ] ลบ useEffect ที่ sync `subagentLogs` ไป store
- [ ] ลบ useEffect ที่ sync `isLoggedIn` ไป store
- [ ] ลบ local state ที่ไม่จำเป็น

**ไฟล์ที่แก้:**
- `src/App.tsx`

### ผลลัพธ์ที่คาดหวัง
- State มีที่เดียวคือ Zustand store
- ลบ sync effects ออกจาก App.tsx
- ลด complexity ใน App.tsx

---

## Phase 2: Fix Prop Drilling with Context
**ระยะเวลา:** 2-3 วัน
**ความเสี่ยง:** ต่ำ
**Branch:** `refactor/phase-2-context`

### เป้าหมาย
- สร้าง Context สำหรับ AgentCard
- ลดจำนวน props ที่ส่งลงมา

### ขั้นตอน

#### 2.1 สร้าง AgentCardContext
- [ ] สร้างไฟล์ `src/contexts/AgentCardContext.tsx`
- [ ] กำหนด interface สำหรับ context value
- [ ] สร้าง Provider component
- [ ] สร้าง custom hook `useAgentCard()`

**ไฟล์ที่สร้าง:**
- `src/contexts/AgentCardContext.tsx`

#### 2.2 แก้ AgentCard ให้ใช้ Context
- [ ] ย้าย state จาก AgentCard ไป Context
- [ ] ลบ props ที่ไม่จำเป็น
- [ ] ใช้ `useAgentCard()` ใน component ลูก

**ไฟล์ที่แก้:**
- `src/components/AgentCard/index.tsx`
- `src/components/AgentCard/AgentHeader.tsx`
- `src/components/AgentCard/GatewayConsole.tsx`
- `src/components/AgentCard/ChatPanel.tsx`
- `src/components/AgentCard/FileManager.tsx`
- `src/components/AgentCard/ShellAccess.tsx`
- `src/components/AgentCard/SubagentMonitor.tsx`

#### 2.3 แก้ AgentPage ให้ส่ง Context
- [ ] ห่อ AgentCard ด้วย AgentCardProvider
- [ ] ส่งข้อมูลผ่าน context แทน props

**ไฟล์ที่แก้:**
- `src/pages/AgentPage.tsx`

### ผลลัพธ์ที่คาดหวัง
- ลด props ใน AgentCard จาก ~15 เหลือ ~3-5
- Component ลูกดึงข้อมูลจาก context แทน props
- ง่ายต่อการบำรุงรักษา

---

## Phase 3: Consolidate Socket Event Management
**ระยะเวลา:** 1-2 วัน
**ความเสี่ยง:** ปานกลาง
**Branch:** `refactor/phase-3-socket`

### เป้าหมาย
- สร้าง custom hook สำหรับจัดการ socket events
- ใช้ socketManager ในที่เดียว

### ขั้นตอน

#### 3.1 สร้าง useSocketEvents hook
- [ ] สร้างไฟล์ `src/hooks/useSocketEvents.ts`
- [ ] ย้าย socket event handlers จาก App.tsx
- [ ] ย้าย socket event handlers จาก LogViewerTerminal.tsx
- [ ] สร้าง hook ที่จัดการ events ทั้งหมด

**ไฟล์ที่สร้าง:**
- `src/hooks/useSocketEvents.ts`

#### 3.2 แก้ App.tsx ให้ใช้ useSocketEvents
- [ ] ลบ socket event handlers จาก App.tsx
- [ ] ใช้ `useSocketEvents()` hook แทน
- [ ] ลบ local state ที่เกี่ยวกับ socket

**ไฟล์ที่แก้:**
- `src/App.tsx`

#### 3.3 แก้ LogViewerTerminal ให้ใช้ useSocketEvents
- [ ] ลบ socket event handlers จาก LogViewerTerminal.tsx
- [ ] ใช้ `useSocketEvents()` hook แทน
- [ ] ลดความซับซ้อนใน component

**ไฟล์ที่แก้:**
- `src/components/LogViewerTerminal.tsx`

### ผลลัพธ์ที่คาดหวัง
- Socket events จัดการในที่เดียว
- ลด code duplication
- ง่ายต่อการ debug

---

## Phase 4: Improve TypeScript Types
**ระยะเวลา:** 1-2 วัน
**ความเสี่ยง:** ต่ำ
**Branch:** `refactor/phase-4-types`

### เป้าหมาย
- กำหนด type ที่ชัดเจนสำหรับ state และ props
- ลดการใช้ `any`

### ขั้นตอน

#### 4.1 สร้าง Shared Types
- [ ] สร้างไฟล์ `src/types/index.ts`
- [ ] ย้าย types จาก `src/types.ts` ไปไฟล์ใหม่
- [ ] เพิ่ม types ที่ขาดหายไป
- [ ] สร้าง type guards

**ไฟล์ที่สร้าง:**
- `src/types/index.ts`
- `src/types/api.ts`
- `src/types/socket.ts`
- `src/types/agent.ts`

#### 4.2 แก้ `any` types
- [ ] หา `any` ทั้งหมดใน codebase
- [ ] กำหนด type ที่เหมาะสม
- [ ] ทดสอบว่า TypeScript compiles ได้

**ไฟล์ที่แก้:**
- ทุกไฟล์ที่มี `any`

#### 4.3 เพิ่ม Type Safety ใน Store
- [ ] กำหนด return types สำหรับ store actions
- [ ] ใช้ `zustand` middleware สำหรับ type safety

**ไฟล์ที่แก้:**
- `src/stores/useAppStore.ts`

### ผลลัพธ์ที่คาดหวัง
- ลด runtime errors
- IDE autocomplete ทำงานได้ดีขึ้น
- Code มี type safety

---

## Phase 5: Component Decomposition
**ระยะเวลา:** 2-3 วัน
**ความเสี่ยง:** ปานกลาง
**Branch:** `refactor/phase-5-components`

### เป้าหมาย
- แบ่ง components ให้เล็กลง
- ใช้ composition pattern

### ขั้นตอน

#### 5.1 แบ่ง App.tsx
- [ ] สร้าง `AppHeader` component
- [ ] สร้าง `AppRouter` component
- [ ] ลด App.tsx เหลือ ~100 บรรทัด

**ไฟล์ที่สร้าง:**
- `src/components/AppHeader.tsx`
- `src/components/AppRouter.tsx`

**ไฟล์ที่แก้:**
- `src/App.tsx`

#### 5.2 แบ่ง AgentCard
- [ ] สร้าง `AgentTabs` component
- [ ] สร้าง `AgentContent` component
- [ ] สร้าง `AgentModelSelector` component
- [ ] ลด AgentCard index.tsx เหลือ ~100 บรรทัด

**ไฟล์ที่สร้าง:**
- `src/components/AgentCard/AgentTabs.tsx`
- `src/components/AgentCard/AgentContent.tsx`
- `src/components/AgentCard/AgentModelSelector.tsx`

#### 5.3 สร้าง Reusable Components
- [ ] สร้าง `StatusBadge` component
- [ ] สร้าง `ControlButton` component
- [ ] สร้าง `LogViewer` component (แยกจาก LogViewerTerminal)

**ไฟล์ที่สร้าง:**
- `src/components/common/StatusBadge.tsx`
- `src/components/common/ControlButton.tsx`
- `src/components/common/LogViewer.tsx`

### ผลลัพธ์ที่คาดหวัง
- Components เล็กลงและเข้าใจง่าย
- Reusable components
- ง่ายต่อการ test

---

## Phase 6: Testing & Documentation
**ระยะเวลา:** 2-3 วัน
**ความเสี่ยง:** ต่ำ
**Branch:** `refactor/phase-6-testing`

### เป้าหมาย
- เพิ่ม unit tests
- เพิ่ม documentation

### ขั้นตอน

#### 6.1 Setup Testing
- [ ] ติดตั้ง Vitest
- [ ] สร้าง test config
- [ ] สร้าง test utilities

**ไฟล์ที่สร้าง:**
- `vitest.config.ts`
- `src/test-utils.tsx`

#### 6.2 เขียน Tests
- [ ] เขียน tests สำหรับ Zustand store
- [ ] เขียน tests สำหรับ custom hooks
- [ ] เขียน tests สำหรับ components

**ไฟล์ที่สร้าง:**
- `src/stores/__tests__/useAppStore.test.ts`
- `src/hooks/__tests__/useLogStream.test.ts`
- `src/hooks/__tests__/useAuth.test.ts`
- `src/components/__tests__/AgentCard.test.tsx`

#### 6.3 เพิ่ม Documentation
- [ ] เพิ่ม JSDoc comments
- [ ] สร้าง README สำหรับแต่ละ module
- [ ] สร้าง Architecture diagram

**ไฟล์ที่สร้าง:**
- `docs/ARCHITECTURE.md`
- `docs/STATE_MANAGEMENT.md`
- `docs/COMPONENTS.md`

### ผลลัพธ์ที่คาดหวัง
- มี unit tests ครอบคลุม
- Code มี documentation
- ง่ายต่อการ onboard developer ใหม่

---

## Timeline Summary

| Phase | ระยะเวลา | ความเสี่ยง | Branch |
|-------|----------|-----------|--------|
| 1. State Consolidation | 2-3 วัน | ต่ำ | `refactor/phase-1-state-consolidation` |
| 2. Context | 2-3 วัน | ต่ำ | `refactor/phase-2-context` |
| 3. Socket Events | 1-2 วัน | ปานกลาง | `refactor/phase-3-socket` |
| 4. TypeScript Types | 1-2 วัน | ต่ำ | `refactor/phase-4-types` |
| 5. Components | 2-3 วัน | ปานกลาง | `refactor/phase-5-components` |
| 6. Testing & Docs | 2-3 วัน | ต่ำ | `refactor/phase-6-testing` |
| **รวม** | **11-16 วัน** | | |

---

## Best Practices

### Branch Strategy
```bash
# สร้าง branch สำหรับแต่ละ phase
git checkout main
git pull
git checkout -b refactor/phase-1-state-consolidation

# หลังทำเสร็จ merge กลับ main
git checkout main
git merge refactor/phase-1-state-consolidation
git push
```

### Commit Convention
```
refactor(phase-1): migrate useLogStream state to Zustand store

- Remove logData state from useLogStream hook
- Update App.tsx to remove sync effect
- Update components to read from store directly
```

### Testing Checklist
- [ ] `npm run dev` ทำงานได้ปกติ
- [ ] Socket events ทำงานได้ปกติ
- [ ] State updates ทำงานได้ปกติ
- [ ] UI แสดงผลถูกต้อง
- [ ] ไม่มี console errors

### Rollback Plan
- ถ้ามีปัญหา: `git checkout main && git branch -D refactor/phase-X`
- ทุก phase merge เข้า main แยกกัน
- สามารถ rollback แค่ phase ที่มีปัญหาได้

---

## คำถามที่พบบ่อย

### Q: ทำไมต้อง refactor ทีละ phase?
A: เพื่อความปลอดภัย ถ้ามีปัญหาจะได้แก้ไขได้ง่าย และสามารถ rollback ได้

### Q: จะรู้ได้อย่างไรว่า refactor สำเร็จ?
A: ทดสอบหลังแต่ละ phase:
1. `npm run dev` ทำงานได้ปกติ
2. ไม่มี TypeScript errors
3. UI แสดงผลถูกต้อง
4. Socket events ทำงานได้ปกติ

### Q: ถ้ามีปัญหาระหว่าง refactor?
A: ทำตาม rollback plan:
1. `git stash` (ถ้ามี uncommitted changes)
2. `git checkout main`
3. ตรวจสอบปัญหา
4. แก้ไขและลองใหม่

### Q: จะ refactor ไปพร้อมกับ development ใหม่ได้ไหม?
A: แนะนำให้ refactor เสร็จก่อน แล้วค่อยพัฒนา feature ใหม่ แต่ถ้าจำเป็น ให้ merge main เข้า refactor branch เป็นระยะ
