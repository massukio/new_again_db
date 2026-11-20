BEGIN TRANSACTION;
CREATE TABLE plate_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part1 TEXT NOT NULL,
            part2 TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            note TEXT,
            brand TEXT DEFAULT '',
            vip INTEGER DEFAULT 0,
            UNIQUE(part1, part2, phone_number)
        );
INSERT INTO "plate_info" VALUES(1,'ABC','1234','0912345678','老客戶','Toyota',1);
INSERT INTO "plate_info" VALUES(2,'DEF','5678','0923456789','','',0);
INSERT INTO "plate_info" VALUES(3,'ABC','1234','0988777666','第二支電話','',0);
CREATE TABLE wash_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_part1 TEXT NOT NULL,
            plate_part2 TEXT NOT NULL,
            amount INTEGER NOT NULL,
            wash_date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
INSERT INTO "wash_records" VALUES(1,'ABC','1234',300,'2026-03-01','一般洗車','2026-11-20 18:11:37');
INSERT INTO "wash_records" VALUES(2,'ABC','1234',800,'2026-04-01','美容 - 打蠟','2026-11-20 18:11:37');
INSERT INTO "wash_records" VALUES(3,'DEF','5678',500,'2026-04-02','精緻洗車','2026-11-20 18:11:37');
CREATE INDEX idx_wash_date ON wash_records(wash_date)
    ;
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('plate_info',3);
INSERT INTO "sqlite_sequence" VALUES('wash_records',3);
COMMIT;
