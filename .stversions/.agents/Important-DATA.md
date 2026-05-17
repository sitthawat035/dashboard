Dashboard มี 2 version ที่ Syncthing ทั้ง Folder dashboard โดยใช้ .gitignore ( "C:\\Users\\User\\openclaw\\dashboard\\.gitignore" ) ในการแยก version กัน

* PC version Dashboard จะ Run บน PC directory \~/openclaw/dashboard
* Android version Dashboard จะ Run บน termux บนมือถือ directory /storage/emulated/0/syncthing/dashboard ( symlink > \~/dashboard )
Note : เมื่อต้องทำงานเกี่ยวกับ dashboard ให้คำนึงถึง 2 version ห้าม hardcode ที่ใดที่นึง
tailscalte IP สำหรับเชื่อ ssh ระหว่าง terminal
* Android termux 100.110.26.16 ( termux terminal )

PC             100.69.181.45 ( powershell terminal windows และ wls terminal )





Alpha's TASK today
1.จัด UI layout tab socialmedia hub ให้เป็นระเบียบเรียบร้อยให้ดู engine tab เป็น reference แล้วทำให้ทุก ฟีเตอร์สามารทำงานได้จริง ตอนนี้ยังไม่มีอะไรทำงานได้และ UI ยังทับกันตามรูป "C:\\Users\\User\\openclaw\\dashboard\\.agents\\Screenshot\_2026\_0428\_214114.jpg"
---



Note : ให้ใช้ tried workflow skill เป็นพื้นฐาน ( stage 1 analysis  > stage 2 implement > stage 3 Qa ) TASK จะผ่านได้ต่อเมื่อผ stage 3 Qa done verication test  โดยใช้ Broser เข้าไปกดใช้งานบน dashboard จริงๆ ทั้ง 2 version   มี ( tailscal IP )
Rule : ห้าม HARDCODE เด็ดขาด ต้องเขียน code สำหรับโปรเจ็คที่ย้ายไปรันได้ทุกที  env vari

