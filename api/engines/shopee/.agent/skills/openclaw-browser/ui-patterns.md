# UI Patterns Reference

## Common UI Components

### Navigation
- **Navbar/Header**: มักอยู่ด้านบนสุด หา logo ซ้าย, menu ขวา
- **Sidebar**: ด้านซ้ายหรือขวา มักมี collapse button
- **Breadcrumb**: แถว link บอก path ปัจจุบัน
- **Tab bar**: แถว tab ใต้ header

### Buttons
- **Primary**: สีเด่น (blue, green) → action หลัก
- **Secondary**: สีเทาหรือ outline → action รอง
- **Danger**: สีแดง → ลบ/ยกเลิก
- **Icon-only**: ดู tooltip หรือ aria-label เพื่อเข้าใจ function

### Forms
- **Text input**: กล่องสี่เหลี่ยม มีเส้นขอบ
- **Textarea**: กล่องสี่เหลี่ยมใหญ่ มักมี resize handle มุมขวาล่าง
- **Select/Dropdown**: มีลูกศรชี้ลง
- **Checkbox**: กล่องเล็กสี่เหลี่ยม ✓ เมื่อเลือก
- **Radio button**: วงกลมเล็ก ● เมื่อเลือก
- **Toggle/Switch**: แท่งรี เลื่อนซ้าย-ขวา
- **File upload**: ปุ่ม "Browse" หรือ drag & drop zone

### Data Display
- **Table**: แถวและคอลัมน์, มี header row
- **Card**: กล่องมีเงา มักมี title + content + action
- **List**: รายการ bullet หรือ numbered
- **Pagination**: ตัวเลขหน้าหรือ Previous/Next

### Feedback
- **Toast/Snackbar**: popup เล็กๆ มุมหน้าจอ หายเองหลังไม่กี่วิ
- **Modal/Dialog**: popup กลางจอ มี overlay หลัง
- **Alert**: แถบสี (success=เขียว, error=แดง, warning=เหลือง, info=น้ำเงิน)
- **Loading spinner**: วงกลมหมุน หรือ skeleton screen
- **Progress bar**: แถบแสดง % ความคืบหน้า

## Tricky UI Cases

### Infinite Scroll
- ไม่มี pagination → scroll ลงเรื่อยๆ
- สังเกต: content โหลดเพิ่มขึ้นเมื่อ scroll ถึงด้านล่าง
- วิธี: scroll → screenshot → ตรวจว่ามี content ใหม่ → ทำซ้ำ

### Lazy Load Images
- รูปภาพอาจยังไม่โหลด → scroll ผ่านก่อน แล้ว scroll กลับมา
- หรือรอสักครู่แล้ว screenshot ใหม่

### Dynamic Content (SPA)
- URL อาจไม่เปลี่ยนแม้ navigate → ดู content บนหน้าแทน
- รอ loading indicator หายก่อน screenshot

### Sticky Elements
- Header/Footer ที่ติดอยู่เสมอ → อาจบัง element ที่ต้องการ
- แก้: scroll จัดตำแหน่ง element ให้อยู่ในส่วนที่มองเห็น

### iFrame Content
- Content ใน iframe อาจไม่ respond กับ click ปกติ
- ต้อง click ใน iframe ก่อน เพื่อ focus แล้ว interact

### Hover-only Menus
- บาง menu ปรากฏเฉพาะตอน hover → ใช้ keyboard shortcut แทน
- หรือ click ที่ trigger element แล้ว screenshot ทันที
